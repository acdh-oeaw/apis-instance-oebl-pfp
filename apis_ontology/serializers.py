from rest_framework.renderers import serializers
from rdflib import Graph, Literal, URIRef, Namespace
from rdflib.namespace import RDF, RDFS, XSD


class PersonCidocSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        g = Graph()

        # Define namespaces
        crm = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
        apis = Namespace("http://apis.acdh.oeaw.ac.at/")

        g.namespace_manager.bind("crm", crm, replace=True)
        g.namespace_manager.bind("apis", apis, replace=True)

        # Create the Person instance
        person_uri = URIRef(apis[str(instance.id)])
        g.add((person_uri, RDF.type, crm.E21_Person))

        # Add properties
        appellation_uri = URIRef(apis[f"appellation_{instance.id}"])
        g.add((appellation_uri, RDF.type, crm.E41_Appellation))
        g.add((person_uri, crm.P1_is_identified_by, appellation_uri))
        g.add(
            (
                appellation_uri,
                RDFS.label,
                Literal(f"{instance.forename} {instance.surname}"),
            )
        )

        if hasattr(instance, "forename"):
            forename_uri = URIRef(apis[f"forename_{instance.id}"])
            g.add((forename_uri, RDF.type, crm.E41_Appellation))
            g.add((appellation_uri, crm.P106_is_composed_of, forename_uri))
            g.add((forename_uri, RDFS.label, Literal(instance.forename)))

        if hasattr(instance, "surname"):
            surname_uri = URIRef(apis[f"surname_{instance.id}"])
            g.add((surname_uri, RDF.type, crm.E41_Appellation))
            g.add((appellation_uri, crm.P106_is_composed_of, surname_uri))
            g.add((surname_uri, RDFS.label, Literal(instance.surname)))

        if hasattr(instance, "birth_date"):
            birth_event = URIRef(apis[f"birth_{instance.id}"])
            g.add((birth_event, RDF.type, crm.E67_Birth))
            g.add((birth_event, crm.P98_brought_into_life, person_uri))
            g.add(
                (
                    birth_event,
                    crm.P4_has_time_span,
                    Literal(instance.birth_date, datatype=XSD.date),
                )
            )

        if hasattr(instance, "death_date"):
            death_event = URIRef(apis[f"death_{instance.id}"])
            g.add((death_event, RDF.type, crm.E69_Death))
            g.add((death_event, crm.P100_was_death_of, person_uri))
            g.add(
                (
                    death_event,
                    crm.P4_has_time_span,
                    Literal(instance.death_date, datatype=XSD.date),
                )
            )

        # Serialize the graph to RDF/XML
        return g
