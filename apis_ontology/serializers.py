from rest_framework.renderers import serializers
from rdflib import Graph, Literal, URIRef, Namespace
from rdflib.namespace import RDF, RDFS, XSD, OWL, GEO
from apis_core.generic.serializers import GenericHyperlinkedModelSerializer
from apis_core.relations.utils import relation_content_types
from apis_ontology.models import (
    Person,
    Institution,
    PersonPlaceLegacyRelation,
    StarbIn,
    WurdeGeborenIn,
)
from django.conf import settings
from apis_core.apis_metainfo.models import Uri
import re


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

    def create_sameas(self, g, ns, instance, instance_uri):
        # add the ID as APIS Identifier
        apis_id = URIRef(ns.attr[f"apis-identifier/{instance.pk}"])
        g.add((apis_id, RDF.type, ns.crm["E42_Identifier"]))
        g.add((apis_id, RDFS.label, Literal(instance.pk)))
        # APIS internal identifier type
        apis_id_type = URIRef(ns.attr["apis-identifier/type"])
        g.add((apis_id, ns.crm["P2_has_type"], apis_id_type))
        triple = (apis_id_type, RDF.type, ns.crm["E55_Type"])
        if triple not in g:
            g.add(triple)
            g.add((apis_id_type, RDFS.label, Literal("APIS internal identifier")))
        g.add((instance, ns.crm.P1_is_identified_by, apis_id))

        for uri in Uri.objects.filter(object_id=instance.pk):
            uri_ref = URIRef(uri.uri)
            g.add((instance_uri, OWL.sameAs, uri_ref))

            # Extract and store identifiers for specific authority sources

            # GND: matches patterns like 118540238 or 4074195-3
            if "d-nb.info" in uri.uri:
                gnd_match = re.search(r"(?:\/gnd\/)(\d+(?:-\d+)?X?)", uri.uri)
                # GND identifier type
                gnd_id_type = URIRef(ns.attr["gnd-identifier/type"])
                triple = (gnd_id_type, RDF.type, ns.crm["E55_Type"])
                if triple not in g:
                    g.add(triple)
                    g.add((gnd_id_type, RDFS.label, Literal("GND ID")))
                if gnd_match:
                    gnd_id = gnd_match.group(1)
                    gnd_id_uri = URIRef(ns.attr[f"gnd-identifier/{instance.pk}"])
                    g.add((gnd_id_uri, RDF.type, ns.crm["E42_Identifier"]))
                    g.add((gnd_id_uri, RDFS.label, Literal(gnd_id)))
                    g.add((gnd_id_uri, ns.crm["P2_has_type"], gnd_id_type))
                    g.add((instance_uri, ns.crm["P1_is_identified_by"], gnd_id_uri))

            # Wikidata: matches Q followed by numbers
            elif "wikidata.org" in uri.uri:
                wikidata_match = re.search(r"[/:]Q(\d+)", uri.uri)
                # Wikidata identifier type
                wikidata_id_type = URIRef(ns.attr["wikidata-identifier/type"])
                triple = (wikidata_id_type, RDF.type, ns.crm["E55_Type"])
                if triple not in g:
                    g.add(triple)
                    g.add((wikidata_id_type, RDFS.label, Literal("Wikidata ID")))
                if wikidata_match:
                    wikidata_id = f"Q{wikidata_match.group(1)}"
                    wikidata_id_uri = URIRef(
                        ns.attr[f"wikidata-identifier/{instance.pk}"]
                    )
                    g.add((wikidata_id_uri, RDF.type, ns.crm["E42_Identifier"]))
                    g.add((wikidata_id_uri, RDFS.label, Literal(wikidata_id)))
                    g.add((wikidata_id_uri, ns.crm["P2_has_type"], wikidata_id_type))
                    g.add(
                        (instance_uri, ns.crm["P1_is_identified_by"], wikidata_id_uri)
                    )

            # GeoNames: matches numeric IDs
            elif "geonames.org" in uri.uri:
                geonames_match = re.search(r"\/(\d+)(?:\/|$)", uri.uri)
                # GeoNames identifier type
                geonames_id_type = URIRef(ns.attr["geonames-identifier/type"])
                triple = (geonames_id_type, RDF.type, ns.crm["E55_Type"])
                if triple not in g:
                    g.add(triple)
                    g.add((geonames_id_type, RDFS.label, Literal("GeoNames ID")))
                if geonames_match:
                    geonames_id = geonames_match.group(1)
                    geonames_id_uri = URIRef(
                        ns.attr[f"geonames-identifier/{instance.pk}"]
                    )
                    g.add((geonames_id_uri, RDF.type, ns.crm["E42_Identifier"]))
                    g.add((geonames_id_uri, RDFS.label, Literal(geonames_id)))
                    g.add((geonames_id_uri, ns.crm["P2_has_type"], geonames_id_type))
                    g.add(
                        (instance_uri, ns.crm["P1_is_identified_by"], geonames_id_uri)
                    )
        return g


class PlaceCidocSerializer(BaseRDFSerializer):
    def to_representation(self, instance):
        instance = normalize_empty_attributes(instance)
        g, ns = super().to_representation(instance)

        place_uri = URIRef(ns.place[str(instance.id)])
        g.add((place_uri, RDF.type, ns.crm.E53_Place))
        g.add((place_uri, RDFS.label, Literal(str(instance))))

        g = self.create_sameas(g, ns, instance, place_uri)
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
            g.add(
                (
                    place_uri,
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
        g.add((inst_uri, RDFS.label, Literal(str(instance))))

        g = self.create_sameas(g, ns, instance, inst_uri)
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


def add_life_event_place(g, ns, instance, person_uri, event_type, event_uri=None):
    """Add place information for life events (birth or death).

    Args:
        g: RDF graph
        ns: Namespace object
        instance: Person model instance
        person_uri: URI of the person
        event_type: 'birth' or 'death'
        event_uri: Optional pre-existing event URI

    Returns:
        Modified RDF graph
    """
    EVENT_TYPES = {
        "birth": {
            "legacy_label": "geboren in",
            "model": WurdeGeborenIn,
            "crm_type": "E67_Birth",
            "label_template": "Geburt von {}",
            "crm_relation": "P98_brought_into_life",
        },
        "death": {
            "legacy_label": "gestorben in",
            "model": StarbIn,
            "crm_type": "E69_Death",
            "label_template": "Tod von {}",
            "crm_relation": "P100_was_death_of",
        },
    }

    if event_type not in EVENT_TYPES:
        raise ValueError(f"event_type must be one of {list(EVENT_TYPES.keys())}")

    event_config = EVENT_TYPES[event_type]

    def get_place_relation(instance, event_config):
        """Get the place relation for a life event."""
        # Try legacy relation first
        legacy_rel = PersonPlaceLegacyRelation.objects.filter(
            subj_object_id=instance.pk,
            legacy_relation_vocab_label=event_config["legacy_label"],
        ).first()

        if legacy_rel:
            return legacy_rel

        # Try new relation model if exists and no legacy relation found
        if event_config["model"]:
            new_rel = (
                event_config["model"].objects.filter(subj_object_id=instance.pk).first()
            )
            return new_rel

        return None

    rel = get_place_relation(instance, event_config)
    if not rel:
        return g

    if event_uri is None:
        event_uri = URIRef(ns.attr[f"{event_type}_{instance.id}"])
        g.add((event_uri, RDF.type, ns.crm[event_config["crm_type"]]))
        g.add(
            (
                event_uri,
                RDFS.label,
                Literal(event_config["label_template"].format(str(instance))),
            )
        )
        g.add((event_uri, ns.crm[event_config["crm_relation"]], person_uri))

    place_uri = URIRef(ns.place[str(rel.obj_object_id)])
    g.add((event_uri, ns.crm.P7_took_place_at, place_uri))

    return g


class PersonCidocSerializer(BaseRDFSerializer):
    def to_representation(self, instance):
        instance = normalize_empty_attributes(instance)
        g, ns = super().to_representation(instance)

        person_uri = URIRef(ns.person[str(instance.id)])
        g.add((person_uri, RDF.type, ns.crm.E21_Person))
        g.add((person_uri, RDFS.label, Literal(str(instance))))

        # Add sameAs links
        g = self.create_sameas(g, ns, instance, person_uri)

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
            g.add((birth_event, RDFS.label, Literal(f"Geburt von {str(instance)}")))
            g.add((birth_event, ns.crm.P98_brought_into_life, person_uri))
            g.add((birth_event, ns.crm["P4_has_time-span"], birth_time_span))
            g.add((birth_time_span, RDF.type, ns.crm["E52_Time-Span"]))
            g.add((birth_time_span, RDFS.label, Literal(instance.start_date_written)))
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
            g.add((death_event, RDFS.label, Literal(f"Tod von {str(instance)}")))
            death_time_span = URIRef(ns.attr[f"death_time-span_{instance.id}"])
            g.add((death_event, RDF.type, ns.crm.E69_Death))
            g.add((death_event, ns.crm.P100_was_death_of, person_uri))
            g.add((death_event, ns.crm["P4_has_time-span"], death_time_span))
            g.add((death_time_span, RDF.type, ns.crm["E52_Time-Span"]))
            g.add((death_time_span, RDFS.label, Literal(instance.end_date_written)))
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
        birth_event_param = birth_event if "birth_event" in locals() else None
        death_event_param = death_event if "death_event" in locals() else None
        g = add_life_event_place(
            g, ns, instance, person_uri, "birth", birth_event_param
        )
        g = add_life_event_place(
            g, ns, instance, person_uri, "death", death_event_param
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
        g.add((joining_uri, RDF.type, ns.crm.E85_Joining))
        g.add((joining_uri, RDFS.label, Literal(f"{str(instance)} gestartet")))
        pc_joining_uri = URIRef(ns.attr[f"pc_joining_ev_{instance.id}"])
        memb_type_uri = URIRef(ns.attr[f"kind_member_{instance.id}"])
        g.add((person_uri, ns.crm.P143i_was_joined_by, joining_uri))
        g.add((joining_uri, ns.crm.P01i_is_domain_of, pc_joining_uri))
        g.add((pc_joining_uri, ns.crm.P02_has_range, inst_uri))
        g.add((pc_joining_uri, RDF.type, ns.crm["PC144_joined_with"]))
        g.add((pc_joining_uri, ns.crm.P144_1_kind_of_member, memb_type_uri))
        g.add((memb_type_uri, RDFS.label, Literal(instance.name())))
        g.add((memb_type_uri, RDF.type, ns.crm.E55_Type))
        leaving_uri = URIRef(ns.attr[f"leaving_ev_{instance.id}"])
        g.add((leaving_uri, RDF.type, ns.crm.E86_Leaving))
        g.add((person_uri, ns.crm["P145i_left_by"], leaving_uri))
        g.add((leaving_uri, ns.crm["P146_separated_from"], inst_uri))
        g.add((leaving_uri, RDFS.label, Literal(f"{str(instance)} beendet")))
        if instance.start_date_written is not None:
            joining_time_span_uri = URIRef(
                ns.attr[f"joining_ev_time_span_{instance.id}"]
            )

            g.add((joining_uri, ns.crm["P4_has_time-span"], joining_time_span_uri))
            g.add((joining_time_span_uri, RDF.type, ns.crm["E52_Time-Span"]))
            g.add(
                (
                    joining_time_span_uri,
                    RDFS.label,
                    Literal(instance.start_date_written),
                )
            )
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
            g.add((leaving_uri, ns.crm["P4_has_time-span"], leaving_time_span_uri))
            g.add((leaving_time_span_uri, RDF.type, ns.crm["E52_Time-Span"]))
            g.add(
                (leaving_time_span_uri, RDFS.label, Literal(instance.end_date_written))
            )
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
