import json
import requests
import os
import pathlib

from django.core.management.base import BaseCommand

SRC = "https://apis.acdh.oeaw.ac.at/apis/api"
TOKEN = os.environ.get("TOKEN")
HEADERS = {"Authorization": f"Token {TOKEN}"}


def fetch_sources():
    sources = dict()

    nextpage = f"{SRC}/metainfo/source/?format=json&limit=1000"
    s = requests.Session()
    while nextpage:
        print(nextpage)
        page = s.get(nextpage, headers=HEADERS)
        data = page.json()
        nextpage = data['next']
        for result in data["results"]:
            if result["pubinfo"] == "\u00d6BL 1815-1950, Bd. 1 (Lfg. 2), S. 112f.":
                result["pubinfo"] = "\u00d6BL 1815-1950, Bd. 1 (Lfg. 2, 1954), S. 112f."
            if result["pubinfo"] == "\u00d6BL 1815-1950, Bd. 6 (Lfg. 27), S. 126":
                result["pubinfo"] = "\u00d6BL 1815-1950, Bd. 6 (Lfg. 27, 1974), S. 126"
            print(result["url"])
            sources[result["id"]] = {
                    "orig_filename": result["orig_filename"],
                    "pubinfo": result["pubinfo"],
                    "author": result["author"]
            }
    return sources


class Command(BaseCommand):
    help = "Export text data from legacy APIS instance"

    def handle(self, *args, **options):
        sources = fetch_sources()
        rj = pathlib.Path("sources.json")
        rj.write_text(json.dumps(sources, indent=2))
