from apis_core.utils.rdf import Attribute, Filter, Relation
from apis_core.apis_entities.rdfconfigs.group import (
    E74_GroupFromDNB,
    E74_GroupFromWikidata,
)


class InstitutionFromDNBCustom(E74_GroupFromDNB):
    start_date = None
    start = Attribute("gndo:dateOfEstablishment")
    end_date = None
    end = Attribute("gndo:dateOfTermination")

    located_in = Relation(
        name="apis_ontology.gelegenin",
        value={"curies": "gndo:placeOfBusiness", "obj": "apis_ontology.place"},
    )


name_query = """
SELECT (COALESCE(?label_de, ?label_en, ?label) AS ?name)
WHERE {
?subject a wikibase:Item .
  OPTIONAL{
    ?subject rdfs:label ?label_de .
    FILTER(lang(?label_de) = "de")
  }
  OPTIONAL{
    ?subject rdfs:label ?label_en .
    FILTER(lang(?label_en) = "en")
  }
  OPTIONAL {
  ?subject rdfs:label ?label .}
  }
"""


class InstitutionFromWikidataCustom(E74_GroupFromWikidata):
    wikibase = Filter([("wikibase:directClaim", "wdt:P910")])
    filter_p31_is_q414147 = None

    label = None
    name = Attribute(name_query)
    start = Attribute("wdt:P571")
    end = Attribute("wdt:P576")

    located_in = Relation(
        name="apis_ontology.gelegenin",
        value={"curies": "wdt:P519", "obj": "apis_ontology.place"},
    )
