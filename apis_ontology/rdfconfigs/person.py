from apis_core.apis_entities.rdfconfigs import E21_PersonFromDNB, E21_PersonFromWikidata
from apis_core.utils.rdf import Attribute, Relation


class E21_PersonFromDNBCustom(E21_PersonFromDNB):
    date_of_birth = None
    start = Attribute("gndo:dateOfBirth")
    date_of_death = None
    end = Attribute("gndo:dateOfDeath")
    profession = None
    profession_profession_m2m = Attribute("gndo:professionOrOccupation")
    diedin = Relation(
        name="apis_ontology.starbin",
        values={"curies": "gndo:placeOfDeath", "obj": "apis_ontology.place"},
    )
    bornin = Relation(
        name="apis_ontology.wurdegeborenin",
        values={"curies": "gndo:placeOfBirth", "obj": "apis_ontology.place"},
    )


class E21_PersonFromWikidataCustom(E21_PersonFromWikidata):
    date_of_birth = None
    start = Attribute("wdt:P569")
    date_of_death = None
    end = Attribute("wdt:P570")
    professon = None
    profession_profession_m2m = Attribute("wdt:P106")
    diedin = Relation(
        name="apis_ontology.starbin",
        values={"curies": "wdt:P20", "obj": "apis_ontology.place"},
    )
    borinin = Relation(
        name="apis_ontology.wurdegeborenin",
        values={"curies": "wdt:P19", "obj": "apis_ontology.place"},
    )
