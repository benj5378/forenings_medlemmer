import datetime
from django.conf import settings
from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test

from members.models.activity import Activity
from members.models.activityinvite import ActivityInvite
from members.models.activityparticipant import ActivityParticipant
from members.models.department import Department
from members.models.person import Person
from members.models.waitinglist import WaitingList
from members.utils.user import user_to_person, has_user


@login_required
@user_passes_test(has_user, "/admin_signup/")
def FamilyDetails(request):
    family = user_to_person(request.user).family
    invites = ActivityInvite.objects.filter(
        person__family=family, expire_dtm__gte=timezone.now(), rejected_dtm=None
    )
    open_activities = Activity.objects.filter(
        open_invite=True, signup_closing__gte=timezone.now()
    ).order_by("zipcode")
    participating = ActivityParticipant.objects.filter(
        member__person__family=family
    ).order_by("-activity__start_date")
    waiting_lists = WaitingList.objects.filter(person__family=family)
    children = family.person_set.filter(membertype=Person.CHILD)
    ordered_persons = family.person_set.order_by("membertype").all()

    open_activities_with_persons = []
    # augment open invites with the persons who could join it in the family
    for curActivity in open_activities:
        applicablePersons = curActivity.get_applicable_persons()

        if applicablePersons.exists():
            open_activities_with_persons.append(
                {
                    "id": curActivity.id,
                    "name": curActivity.name,
                    "department": curActivity.department,
                    "persons": applicablePersons,
                }
            )

    # update visited field
    family.last_visit_dtm = timezone.now()
    family.save()

    department_children_waiting = {"departments": {}}
    loop_counter = 0
    for department in Department.objects.filter(closed_dtm=None):
        department_children_waiting["departments"][loop_counter] = {}
        department_children_waiting["departments"][loop_counter]["object"] = department
        department_children_waiting["departments"][loop_counter]["children_status"] = {}
        for child in children:
            department_children_waiting["departments"][loop_counter]["children_status"][
                child.pk
            ] = {}
            department_children_waiting["departments"][loop_counter]["children_status"][
                child.pk
            ]["object"] = child
            department_children_waiting["departments"][loop_counter]["children_status"][
                child.pk
            ]["firstname"] = child.firstname()
            department_children_waiting["departments"][loop_counter]["children_status"][
                child.pk
            ][
                "waiting"
            ] = False  # default not waiting
            for current_wait in waiting_lists:
                if (
                    current_wait.department == department
                    and current_wait.person == child
                ):
                    # child is waiting on this department
                    department_children_waiting["departments"][loop_counter][
                        "children_status"
                    ][child.pk]["waiting"] = True
                    break
        loop_counter = loop_counter + 1

    context = {
        "family": family,
        "invites": invites,
        "participating": participating,
        "open_activities": open_activities_with_persons,
        "need_confirmation": family.confirmed_dtm is None
        or family.confirmed_dtm
        < timezone.now()
        - datetime.timedelta(days=settings.REQUEST_FAMILY_VALIDATION_PERIOD),
        "request_parents": family.person_set.exclude(membertype=Person.CHILD).count()
        < 1,
        "department_children_waiting": department_children_waiting,
        "children": children,
        "ordered_persons": ordered_persons,
    }
    return render(request, "members/family_details.html", context)
