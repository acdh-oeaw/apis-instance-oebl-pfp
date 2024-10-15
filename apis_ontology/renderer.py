from rest_framework import renderers
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD


class CIDOCCRMRenderer(renderers.BaseRenderer):
    media_type = "application/rdf+xml"
    format = "rdf"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        g = Graph()

        # Define namespaces
        crm = g.namespace("http://www.cidoc-crm.org/cidoc-crm/")
        ex = g.namespace("http://example.org/")

        # Create the Person instance
        person_uri = URIRef(ex[str(data["id"])])
        g.add((person_uri, RDF.type, crm.E21_Person))

        # Add properties
        appellation_uri = URIRef(ex[f"appellation_{data['id']}"])
        g.add((appellation_uri, RDF.type, crm.E41_Appellation))
        g.add((person_uri, crm.P1_is_identified_by, appellation_uri))
        g.add(
            (
                appellation_uri,
                RDFS.label,
                Literal(f"{data['forename']} {data['surname']}"),
            )
        )

        if "forename" in data:
            forename_uri = URIRef(ex[f"forename_{data['id']}"])
            g.add((forename_uri, RDF.type, crm.E41_Appellation))
            g.add((appellation_uri, crm.P106_is_composed_of, forename_uri))
            g.add((forename_uri, RDFS.label, Literal(data["forename"])))

        if "surname" in data:
            surname_uri = URIRef(ex[f"surname_{data['id']}"])
            g.add((surname_uri, RDF.type, crm.E41_Appellation))
            g.add((appellation_uri, crm.P106_is_composed_of, surname_uri))
            g.add((surname_uri, RDFS.label, Literal(data["surname"])))

        if "birth_date" in data:
            birth_event = URIRef(ex[f"birth_{data['id']}"])
            g.add((birth_event, RDF.type, crm.E67_Birth))
            g.add((birth_event, crm.P98_brought_into_life, person_uri))
            g.add(
                (
                    birth_event,
                    crm.P4_has_time_span,
                    Literal(data["birth_date"], datatype=XSD.date),
                )
            )

        if "death_date" in data:
            death_event = URIRef(ex[f"death_{data['id']}"])
            g.add((death_event, RDF.type, crm.E69_Death))
            g.add((death_event, crm.P100_was_death_of, person_uri))
            g.add(
                (
                    death_event,
                    crm.P4_has_time_span,
                    Literal(data["death_date"], datatype=XSD.date),
                )
            )

        # Serialize the graph to RDF/XML
        return g.serialize(format="xml")
