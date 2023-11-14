from django.db.models.functions import Collate

from .models import Person


PersonListViewQueryset = Person.objects.all().order_by(Collate("name", "en-x-icu"))
