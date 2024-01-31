import json
import urllib
from django.db.models.functions import Collate
from django.conf import settings

from .models import Person

DB_COLLATION = 'binary' if 'sqlite' in settings.DATABASES['default']['ENGINE'] else 'en-x-icu'

PersonListViewQueryset = Person.objects.all().order_by(Collate("name", DB_COLLATION), Collate("first_name", DB_COLLATION))


class PersonExternalAutocomplete:

    def extract(self, res):
        value = lambda x: x["value"]
        labels = list(map(value, res["http://www.w3.org/2000/01/rdf-schema#label"]))
        return {
            "id": res["id"],
            "text": labels[0],
            "selected_text": labels[0]
        }

    def get_results(self, q):
        if q:
            endpoint = "https://enrich.acdh.oeaw.ac.at/entityhub/site/gndPersons/find"
            data = urllib.parse.urlencode({'name': f"*{q}*"})
            data = data.encode('ascii')
            with urllib.request.urlopen(endpoint, data) as f:
                data = json.loads(f.read())
                results = list(map(self.extract, data.get("results", [])))
                print(results)
                return results
        return {}
