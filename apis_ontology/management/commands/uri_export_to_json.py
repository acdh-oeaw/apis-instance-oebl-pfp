import json
import requests
import os
import pathlib

from django.core.management.base import BaseCommand

SRC = "https://apis.acdh.oeaw.ac.at/apis/api"
TOKEN = os.environ.get("TOKEN")
HEADERS = {"Authorization": f"Token {TOKEN}"}


def fetch_uris():
    uris = dict()

    nextpage = f"{SRC}/metainfo/uri/?format=json&limit=1000"
    s = requests.Session()
    while nextpage:
        print(nextpage)
        page = s.get(nextpage, headers=HEADERS)
        data = page.json()
        nextpage = data['next']
        for result in data['results']:
            if result["uri"] == "https://apis-edits.acdh-dev.oeaw.ac.at/entity/None/":
                continue
            if result["uri"] == "":
                continue
            del result["url"]
            uri_id = result.pop("id")
            if entity := result.get("entity"):
                result["entity"] = entity["id"]
            uris[uri_id] = result
    return uris


class Command(BaseCommand):
    help = "Export text data from legacy APIS instance"

    def handle(self, *args, **options):
        rj = pathlib.Path("uris.json")
        rj.write_text(json.dumps(fetch_uris(), indent=2))
