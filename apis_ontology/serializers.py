from rest_framework.renderers import serializers
from rdflib import Graph, Literal, URIRef, Namespace
from rdflib.namespace import RDF, RDFS, XSD, OWL, GEO
from apis_core.generic.serializers import GenericHyperlinkedModelSerializer
from apis_core.relations.utils import relation_content_types
from apis_ontology.models import Person, Institution
from django.conf import settings
from apis_core.apis_metainfo.models import Uri


def normalize_empty_attributes(instance):
    """
    Normalize empty string attributes of a Django model instance to None.
    Only processes actual model fields, not methods or private attributes.

    Args:
        instance: Django model instance

    Returns:
        The modified instance with empty strings converted to None
    """
    for field in instance._meta.fields:
        value = getattr(instance, field.name, None)
        if isinstance(value, str) and not value:
            setattr(instance, field.name, None)
    return instance


# Dynamically create and add serializer classes to this module
for ct in relation_content_types():
    cls = ct.model_class()
    if cls.__name__ == "Relation":
        continue
    serializer_class = type(
        f"{cls.__name__}Serializer",
        (GenericHyperlinkedModelSerializer,),
        {
            "__module__": __name__,
            "Meta": type("Meta", (), {"model": cls, "fields": "__all__"}),
        },
    )
    # Add the new serializer class to the module globals
    globals()[f"{cls.__name__}Serializer"] = serializer_class


class Namespaces:
    """Container class for RDF namespaces"""

    def __init__(self, base_uri):
        self.crm = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
        self.place = Namespace(f"{base_uri}apis_ontology.place/")
        self.appellation = Namespace(f"{base_uri}appellation/")
        self.inst = Namespace(f"{base_uri}apis_ontology.institution/")
        self.attr = Namespace(f"{base_uri}attributes/")
        self.person = Namespace(f"{base_uri}apis_ontology.person/")

    def bind_to_graph(self, g):
        """Bind all namespaces to the given graph"""
        g.namespace_manager.bind("crm", self.crm, replace=True)
        g.namespace_manager.bind("oebl-place", self.place, replace=True)
        g.namespace_manager.bind("oebl-appellation", self.appellation, replace=True)
        g.namespace_manager.bind("oebl-attr", self.attr, replace=True)
        g.namespace_manager.bind("oebl-person", self.person, replace=True)
        g.namespace_manager.bind("oebl-inst", self.inst, replace=True)
        g.namespace_manager.bind("owl", OWL, replace=True)
        g.namespace_manager.bind("geo", GEO, replace=True)


class BaseRDFSerializer(serializers.BaseSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.g = None
        self.ns = None

    def to_representation(self, instance):
        g = Graph()
        base_uri = getattr(
            settings, "APIS_BASE_URI", self.context["request"].build_absolute_uri("/")
        )
        if not base_uri.endswith("/"):
            base_uri += "/"

        # Create namespaces instance
        ns = Namespaces(base_uri)
        ns.bind_to_graph(g)

        return g, ns

    def create_sameas(self, g, instance, instance_uri):
        for uri in Uri.objects.filter(object_id=instance.pk):
            uri_ref = URIRef(uri.uri)
            g.add((instance_uri, OWL.sameAs, uri_ref))
        return g


class PlaceCidocSerializer(BaseRDFSerializer):
    def to_representation(self, instance):
        instance = normalize_empty_attributes(instance)
        g, ns = super().to_representation(instance)

        # Create the Person instance
        place_uri = URIRef(ns.place[str(instance.id)])
        g.add((place_uri, RDF.type, ns.crm.E53_Place))

        g = self.create_sameas(g, instance, place_uri)
        # Add sameAs links

        # Add properties
        appellation_uri = URIRef(ns.appellation[str(instance.id)])
        g.add((appellation_uri, RDF.type, ns.crm.E33_E41_Linguistic_Appellation))
        g.add((place_uri, ns.crm.P1_is_identified_by, appellation_uri))
        g.add(
            (
                appellation_uri,
                RDFS.label,
                Literal(f"{instance.label}"),
            )
        )
        if instance.latitude is not None and instance.longitude is not None:
            node_spaceprimitive = ns.attr[f"spaceprimitive.{instance.id}"]
            g.add((place_uri, ns.crm.P168_place_is_defined_by, node_spaceprimitive))
            g.add((node_spaceprimitive, RDF.type, ns.crm.E94_Space_Primitive))
            g.add(
                (
                    node_spaceprimitive,
                    ns.crm.P168_place_is_defined_by,
                    Literal(
                        (
                            f"Point ( {'+' if instance.longitude > 0 else ''}{instance.longitude} {'+' if instance.latitude > 0 else ''}{instance.latitude} )"
                        ),
                        datatype=GEO.wktLiteral,
                    ),
                )
            )
        return g


class InstitutionCidocSerializer(BaseRDFSerializer):
    def to_representation(self, instance):
        instance = normalize_empty_attributes(instance)
        g, ns = super().to_representation(instance)

        # Create the Person instance
        inst_uri = URIRef(ns.inst[str(instance.id)])
        g.add((inst_uri, RDF.type, ns.crm.E74_Group))

        g = self.create_sameas(g, instance, inst_uri)
        # Add sameAs links

        # Add properties
        appellation_uri = URIRef(ns.appellation[str(instance.id)])
        g.add((appellation_uri, RDF.type, ns.crm.E33_E41_Linguistic_Appellation))
        g.add((inst_uri, ns.crm.P1_is_identified_by, appellation_uri))
        g.add(
            (
                appellation_uri,
                RDFS.label,
                Literal(f"{instance.name}"),
            )
        )
        return g


class PersonCidocSerializer(BaseRDFSerializer):
    def to_representation(self, instance):
        instance = normalize_empty_attributes(instance)
        g, ns = super().to_representation(instance)

        person_uri = URIRef(ns.person[str(instance.id)])
        g.add((person_uri, RDF.type, ns.crm.E21_Person))

        g = self.create_sameas(g, instance, person_uri)
        # Add sameAs links

        # Add properties
        appellation_uri = URIRef(ns.appellation[str(instance.id)])
        g.add((appellation_uri, RDF.type, ns.crm.E33_E41_Linguistic_Appellation))
        g.add((person_uri, ns.crm.P1_is_identified_by, appellation_uri))
        g.add(
            (
                appellation_uri,
                RDFS.label,
                Literal(f"{instance.forename} {instance.surname}"),
            )
        )

        if hasattr(instance, "forename"):
            forename_uri = URIRef(ns.appellation[f"forename_{instance.id}"])
            g.add((forename_uri, RDF.type, ns.crm.E33_E41_Linguistic_Appellation))
            g.add((appellation_uri, ns.crm.P106_is_composed_of, forename_uri))
            g.add((forename_uri, RDFS.label, Literal(instance.forename)))

        if hasattr(instance, "surname"):
            surname_uri = URIRef(ns.appellation[f"surname_{instance.id}"])
            g.add((surname_uri, RDF.type, ns.crm.E33_E41_Linguistic_Appellation))
            g.add((appellation_uri, ns.crm.P106_is_composed_of, surname_uri))
            g.add((surname_uri, RDFS.label, Literal(instance.surname)))

        if instance.start_date_written is not None:
            birth_event = URIRef(ns.attr[f"birth_{instance.id}"])
            birth_time_span = URIRef(ns.attr[f"birth_time-span_{instance.id}"])
            g.add((birth_event, RDF.type, ns.crm.E67_Birth))
            g.add((birth_event, ns.crm.P98_brought_into_life, person_uri))
            g.add((birth_event, ns.crm["P4_has_time-span"], birth_time_span))
            g.add((birth_time_span, RDF.type, ns.crm["E52_Time-Span"]))
            g.add(
                (
                    birth_time_span,
                    ns.crm.P82a_begin_of_the_begin,
                    Literal(instance.start_date, datatype=XSD.date)
                    if instance.start_date is not None
                    else Literal(instance.start_date_written),
                )
            )
            g.add(
                (
                    birth_time_span,
                    ns.crm.P82b_end_of_the_end,
                    Literal(instance.start_date, datatype=XSD.date)
                    if instance.start_date is not None
                    else Literal(instance.start_date_written),
                )
            )

        if instance.end_date_written is not None:
            death_event = URIRef(ns.attr[f"death_{instance.id}"])
            death_time_span = URIRef(ns.attr[f"death_time-span_{instance.id}"])
            g.add((death_event, RDF.type, ns.crm.E69_Death))
            g.add((death_event, ns.crm.P100_was_death_of, person_uri))
            g.add((death_event, ns.crm["P4_has_time-span"], death_time_span))
            g.add((death_time_span, RDF.type, ns.crm["E52_Time-Span"]))
            g.add(
                (
                    death_time_span,
                    ns.crm.P82a_begin_of_the_begin,
                    Literal(instance.end_date, datatype=XSD.date)
                    if instance.end_date is not None
                    else Literal(instance.end_date_written),
                )
            )
            g.add(
                (
                    death_time_span,
                    ns.crm.P82b_end_of_the_end,
                    Literal(instance.end_date, datatype=XSD.date)
                    if instance.end_date is not None
                    else Literal(instance.end_date_written),
                )
            )

        # Serialize the graph to RDF/XML
        return g


class PersonInstitutionCidocBaseSerializer(BaseRDFSerializer):
    def to_representation(self, instance):
        instance = normalize_empty_attributes(instance)
        g, ns = super().to_representation(instance)

        person_id = (
            instance.obj_oject_id
            if instance.obj_content_type.model == "person"
            else instance.subj_object_id
        )
        # Create the Person instance
        person_uri = URIRef(ns.person[str(person_id)])
        g.add(
            (person_uri, RDF.type, ns.crm.E21_Person)
        )  # maybe remove that as also in detail view of person
        inst_id = (
            instance.subj_object_id
            if instance.subj_object_id != person_id
            else instance.obj_object_id
        )
        inst_uri = URIRef(ns.inst[str(inst_id)])
        g.add((inst_uri, RDF.type, ns.crm.E74_Group))
        joining_uri = URIRef(ns.attr[f"joining_ev_{instance.id}"])
        pc_joining_uri = URIRef(ns.attr[f"pc_joining_ev_{instance.id}"])
        memb_type_uri = URIRef(ns.attr[f"kind_member_{instance.id}"])
        g.add((person_uri, ns.crm.P143i_was_joined_by, joining_uri))
        g.add((joining_uri, ns.crm.P01i_is_domain_of, pc_joining_uri))
        g.add((pc_joining_uri, ns.crm.P02_has_range, inst_uri))
        g.add((pc_joining_uri, ns.crm.P144_1_kind_of_member, memb_type_uri))
        g.add((memb_type_uri, RDFS.label, Literal(instance.name())))
        if instance.start_date_written is not None:
            joining_time_span_uri = URIRef(
                ns.attr[f"joining_ev_time_span_{instance.id}"]
            )

            g.add((joining_uri, ns.crm["P4_has_time-span"], joining_time_span_uri))
            g.add((joining_time_span_uri, RDF.type, ns.crm["E52_Time-Span"]))
            g.add(
                (
                    joining_time_span_uri,
                    ns.crm.P82a_begin_of_the_begin,
                    Literal(instance.start_date, datatype=XSD.date)
                    if instance.start_date is not None
                    else Literal(instance.start_date_written),
                )
            )
            g.add(
                (
                    joining_time_span_uri,
                    ns.crm.P82b_end_of_the_end,
                    Literal(instance.start_date, datatype=XSD.date)
                    if instance.start_date is not None
                    else Literal(instance.start_date_written),
                )
            )
        if instance.end_date_written is not None:
            leaving_time_span_uri = URIRef(
                ns.attr[f"leaving_ev_time_span_{instance.id}"]
            )
            leaving_uri = URIRef(ns.attr[f"leaving_ev_{instance.id}"])
            g.add((leaving_uri, RDF.type, ns.crm.E86_Leaving))
            g.add((leaving_uri, ns.crm["P4_has_time-span"], leaving_time_span_uri))
            g.add((leaving_time_span_uri, RDF.type, ns.crm["E52_Time-Span"]))
            g.add(
                (
                    leaving_time_span_uri,
                    ns.crm.P82a_begin_of_the_begin,
                    Literal(instance.end_date, datatype=XSD.date)
                    if instance.end_date is not None
                    else Literal(instance.end_date_written),
                )
            )
            g.add(
                (
                    leaving_time_span_uri,
                    ns.crm.P82b_end_of_the_end,
                    Literal(instance.end_date, datatype=XSD.date)
                    if instance.end_date is not None
                    else Literal(instance.end_date_written),
                )
            )
        return g


for ct in relation_content_types(combination=(Person, Institution)):
    cls = ct.model_class()
    serializer_class = type(
        f"{cls.__name__}CidocSerializer",
        (PersonInstitutionCidocBaseSerializer,),
        {
            "__module__": __name__,
        },
    )
    # Add the new serializer class to the module globals
    globals()[f"{cls.__name__}CidocSerializer"] = serializer_class
