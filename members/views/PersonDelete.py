import uuid
import json

from django.http import Http404, HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404

from members.models.person import Person
from members.models.family import Family


def PersonDelete(request, unique, id):
    try:
        unique = uuid.UUID(unique)
    except ValueError:
        return HttpResponseBadRequest("Familie id er ugyldigt")

    person = get_object_or_404(Person, pk=id)
    if person.family.unique != unique:
        raise Http404("Person eksisterer ikke")
    if request.method == 'POST':
        data = json.loads(request.body.decode(request.encoding))  # Decode post bytes with request encoding and parse it as JSON
        if data["action"] == "delete":
            family = get_object_or_404(Family, unique=unique)
            print(len(family.person_set.all()))
            # Check if there is only one parent of guardian left.
            # If there is one or less and the person whom is requested for a deletion is parent or guardien, then interrupt the deletion
            if person.membertype in {'PA', 'GU'} and 1 >= (len(family.person_set.filter(membertype=Person.PARENT)) + len(family.person_set.filter(membertype=Person.GUARDIAN))):
                return HttpResponse("Sletning afbrudt: Der skal altid være mindst én værge eller forældre")
            # If there is not at least one person in the system, then FamilyDetails will crash.
            # Therefor; check that there is at least one person in the family, else: interrupt deletion
            elif 1 >= len(family.person_set.all()):
                return HttpResponse("Sletning afbrudt: Der skal altid være mindst en person indskrevet i systemet")
            Person.objects.filter(id=id).delete()  # Delete person
            return HttpResponse("Success")
    else:
        return HttpResponseBadRequest("Bad request")
    return HttpResponse("Error")
