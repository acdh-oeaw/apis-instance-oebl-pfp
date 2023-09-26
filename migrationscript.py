#!/usr/bin/python3

import requests
import getpass

SRC="https://apis.acdh.oeaw.ac.at/apis/api"
DST="https://oebl-pnp.acdh-dev.oeaw.ac.at"
#DST="http://localhost:8000"
DSTAPISAPI=f"{DST}/apis/api"
DSTCSTMAPI=f"{DST}/custom-api/writeuri"


from requests.auth import HTTPBasicAuth

user = input("Username:")
password = getpass.getpass()

basic = HTTPBasicAuth(user, password)

entitytypes = ['event', 'institution', 'person', 'place', 'work']
for entitytype in entitytypes:
    nextpage = f"{SRC}/entities/{entitytype}/?format=json"
    while nextpage:
        page = requests.get(nextpage)
        data = page.json()
        nextpage = data['next']
        for result in data["results"]:
            result_id = result["id"]
            if "kind" in result and result["kind"] is not None:
                result["kind"] = result["kind"]["label"]
            if "profession" in result and result["profession"] is not None:
                result["profession"] = ",".join([x["label"] for x in result["profession"]])
            # we first try to overwrite existing entries
            response = requests.put(f"{DSTAPISAPI}/ontology/{entitytype}/{result_id}/", result, auth=basic)
            # if no entry with that id exists, we create a new one
            if response.status_code == 404:
                response = requests.post(f"{DSTAPISAPI}/ontology/{entitytype}/", result, auth=basic)
            if not response:
                print(response.text)
                print(result)


nextpage = f"{SRC}/metainfo/uri/?format=json"
while nextpage:
    page = requests.get(nextpage)
    data = page.json()
    nextpage = data['next']
    for result in data["results"]:
        result_id = result["id"]
        result["root_object"] = result["entity"]["id"]
        del result["entity"]
        # we first try to overwrite existing entries
        response = requests.put(f"{DSTCSTMAPI}/{result_id}/", result, auth=basic)
        # if no entry with that id exists, we create a new one
        if response.status_code == 404:
            response = requests.post(f"{DSTCSTMAPI}/", result, auth=basic)
        if not response:
            print(response.text)
            print(result)
