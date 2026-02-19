from apis_core.utils.rdf import Attribute, Filter


class ProfessionFromDNB:
    gndsubjectcategory = Filter(
        [
            (
                "gndo:gndSubjectCategory",
                "<https://d-nb.info/standards/vocab/gnd/gnd-sc#9.4ab>",
            )
        ]
    )

    name = Attribute(["gndo:preferredNameForTheSubjectHeading"])


namequery = """
SELECT (COALESCE(?label_de, ?label_en, ?label) as ?label)
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


class ProfessionFromWikidata:
    q28640 = Filter([("wdt:P31", "wd:Q28640")])

    name = Attribute([namequery])
    same_as = Attribute(["wdt:P227"])
