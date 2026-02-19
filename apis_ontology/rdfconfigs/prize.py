from apis_core.utils.rdf import Attribute, Relation, Filter


class PrizeFromDNB:
    subjectheadingsensostricto = Filter(
        [("rdf:type", "gndo:SubjectHeadingSensoStricto")]
    )

    name = Attribute("gndo:preferredNameForTheSubjectHeading")
    same_as = Attribute("owl:sameAs")


namequery = """
SELECT (COALESCE(?label_de, ?label_en, ?label) as ?name)
	WHERE {
		?subject rdfs:label ?label
		OPTIONAL{
			?subject rdfs:label ?label_de
			FILTER(LANG(?label_de) = "de")
			}
		OPTIONAL{
			?subject rdfs:label ?label_en
			FILTER(LANG(?label_en) = "en")
}
}
"""


class PrizeFromWikidata:
    q618779 = Filter([("wdt:P31", "wd:Q618779")])
    q11448906 = Filter([("wdt:P31", "wd:Q11448906")])

    name = Attribute(namequery)
    start = Attribute(["wdt:P571", "wdt:P580"])
    same_as = Attribute(["wdtn:P227", "wdtn:P1566", "wdtn:P214", "wdtn:P244"])
