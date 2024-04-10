import json
import requests
import os
import pathlib

from django.core.management.base import BaseCommand

SRC = "https://apis.acdh.oeaw.ac.at/apis/api"
TOKEN = os.environ.get("TOKEN")
HEADERS = {"Authorization": f"Token {TOKEN}"}


def fetch_texts():
    texts = dict()

    nextpage = f"{SRC}/metainfo/text/?format=json&limit=5000"
    s = requests.Session()
    while nextpage:
        print(nextpage)
        page = s.get(nextpage, headers=HEADERS)
        data = page.json()
        nextpage = data['next']
        for result in data['results']:
            ttype = None
            if result["kind"] is not None:
                ttype = result["kind"]["label"]
                if ttype == "Soziale Herkunft: ":
                    ttype = "Soziale Herkunft"
                if ttype == "\u00dcbersiedlungen, Emigration, Remigration":
                    ttype = "\u00dcbersiedlung, Emigration, Remigration"
            # we ignore the text types
            # * Place description ÖBL (2)
            # * Place review comments and (236)
            # * Commentary Staribacher (5811)
            # See: https://github.com/acdh-oeaw/apis-instance-oebl-pnp/issues/172
            if ttype not in ["Place description ÖBL", "Place review comments", "Commentary Staribacher", None]:
                texts[result["id"]] = {"text": result["text"], "type": ttype}
            print(result['url'])
    return texts


class Command(BaseCommand):
    help = "Export text data from legacy APIS instance"

    def handle(self, *args, **options):
        texts = fetch_texts()
        rj = pathlib.Path("texts.json")
        rj.write_text(json.dumps(texts, indent=2))
