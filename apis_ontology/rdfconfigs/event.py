from apis_core.utils.rdf import Attribute, Filter, Relation


class EventFromDNB:
    conference_or_event = Filter([("rdf:type", "gndo:ConferenceOrEvent")])
    historical_single_event = Filter([("rdf:type", "gndo:HistoricSingleEventOrEra")])

    name = Attribute(
        [
            "gndo:preferredNameForTheConferenceOrEvent",
            "gndo:preferredNameForTheSubjectHeading",
        ]
    )
    start = Attribute(
        [
            "gndo:dateOfEstablishment",
            "gndo:dateOfProduction",
            "gndo:dateOfConferenceOrEvent",
        ]
    )
    end = Attribute("gndo:dateOfTermination")
    same_as = Attribute("owl:sameAs")

    happenedin = Relation(
        name="apis_ontology.fandstattin",
        value={
            "curies": ["gndo:place", "gndo:placeOfConferenceOrEvent"],
            "obj": "apis_ontology.place",
        },
    )
