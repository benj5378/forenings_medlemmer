#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings
from quickpay_api_client import QPClient
from django.core.urlresolvers import reverse


class QuickpayTransaction(models.Model):
    payment = models.ForeignKey('Payment')
    link_url =  models.CharField('Link til Quickpay formular',max_length=512, blank=True)
    transaction_id = models.IntegerField('Transaktions ID', null=True, default=None)
    refunding = models.ForeignKey('self', null=True, default=None, on_delete=models.PROTECT)
    amount_ore = models.IntegerField('Beløb i øre', default=0) # payments to us is positive
    order_id = models.CharField('Quickpay order id',max_length=20, blank=True, unique=True)

    def save(self, *args, **kwargs):
        """ On creation make quickpay order_id from payment id """
        if(self.pk is None):
            if settings.DEBUG:
                prefix = 'test'
            else:
                prefix = 'prod'
            self.order_id = prefix + '%06d' % self.payment.pk
        return super(QuickpayTransaction, self).save(*args, **kwargs)

    # method requests payment URL from Quickpay.
    # return_url is the url which Quickpay redirects to (used for both success and failure)
    def get_link_url(self, return_url=''):
        if(self.link_url == ''):
            #request only if not already requested
            client = QPClient(":{0}".format(settings.QUICKPAY_API_KEY))

            parent = self.payment.family.get_first_parent()

            address = {'name' : parent.name,
                       'street' : parent.address(),
                       'city' : parent.city,
                       'zip_code' : parent.zipcode,
                       'att' : self.payment.family.email,
                       'country_code' : 'DNK'
                       }

            variables = address.copy()
            variables['family'] = self.payment.family.email
            if(self.payment.person):
                variables['person_name'] = self.payment.person.name
            if(self.payment.activity):
                variables['activity_department'] = self.payment.activity.department.name
                variables['activity_name'] = self.payment.activity.name

            try:
                if(self.transaction_id is None):
                    activity = client.post('/payments', currency='DKK', order_id=self.order_id, variables=variables, invoice_address=address, shipping_address=address)
                    self.transaction_id = activity['id']
                    self.save()

                if(self.transaction_id is None):
                    raise Exception('we did not get a transaction_id')

                link = client.put(
                    '/payments/{0}/link'.format(self.transaction_id),
                    amount=self.payment.amount_ore,
                    id=self.transaction_id,
                    continueurl=return_url,
                    cancelurl=return_url,
                    customer_email=self.payment.family.email,
                    autocapture=True
                    )

                self.link_url = link['url']
                self.save()
            except:
                # Something went wrong talking to quickpay - ask people to come back later
                return reverse('payment_gateway_error_view', kwargs={'unique':self.payment.family.unique})

        return self.link_url

    # If callback was lost - we can get transaction status directly
    def update_status(self):
        client = QPClient(":{0}".format(settings.QUICKPAY_API_KEY))

        # get payment id from order id
        transactions = client.get('/payments', order_id=self.order_id)

        if(len(transactions) > 0):
            transaction = transactions[0]

            if transaction['state'] == 'processed' and transaction['accepted']:
                self.payment.set_confirmed()
            if transaction['state'] == 'rejected' and not transaction['accepted']:
                self.payment.set_rejected(repr(transaction))

    def __str__(self):
        return str(self.payment.family.email) + " - QuickPay orderid: '" + str(self.order_id) + "' confirmed: '" + str(self.payment.confirmed_dtm) + "'"
