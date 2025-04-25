import re
from typing import Any

from django.conf import settings
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import GEO, OWL, RDF, RDFS, XSD
from rest_framework.renderers import serializers

from apis_core.apis_entities.serializers import E21_PersonCidocSerializer
from apis_core.apis_metainfo.models import Uri
from apis_core.generic.utils.rdf_namespace import ATTRIBUTES, CRM
from apis_core.relations.utils import relation_content_types
from apis_ontology.models import (
    Institution,
    Person,
    PersonPlaceLegacyRelation,
    StarbIn,
    WurdeGeborenIn,
)


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


def add_time_spans(g: Graph, ts_node: URIRef, instance: Any, field: str) -> Graph:
    """Add time span information to an RDF graph.

    This function adds time span triples to the given RDF graph based on date fields
    from the provided instance. It handles cases where direct date fields are missing
    but a sort date is available.

    Args:
        g: The RDF graph to add triples to
        ts_node: The time span node URI reference
        instance: The model instance containing date fields
        ns: Namespace manager for instance
        field: Field prefix for date fields (e.g., 'start' or 'end')

    Returns:
        The modified RDF graph
    """
    # Get date values with safe defaults
    date_from = getattr(instance, f"{field}_date_from", None)
    date_to = getattr(instance, f"{field}_date_to", None)
    date_sort = getattr(instance, f"{field}_date_sort", None)

    # Use sort date as fallback if both from/to dates are missing
    if (date_from is None and date_to is None) and date_sort is not None:
        date_from = date_sort
        date_to = date_sort

    crm_namespace = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
    g.namespace_manager.bind("crm", crm_namespace, replace=True)
    # Only add time span information if we have both dates
    if date_from is not None and date_to is not None:
        # Add begin and end date triples
        g.add(
            (
                ts_node,
                crm_namespace.P82a_begin_of_the_begin,
                Literal(date_from, datatype=XSD.date),
            )
        )
        g.add(
            (
                ts_node,
                crm_namespace.P82b_end_of_the_end,
                Literal(date_to, datatype=XSD.date),
            )
        )

        # Add label and type triples
        try:
            # Try to get the field value for the label
            field_value = getattr(instance, field, str(field))
            g.add((ts_node, RDFS.label, Literal(field_value)))
        except (AttributeError, TypeError):
            # Fallback to using the field name if attribute doesn't exist
            g.add((ts_node, RDFS.label, Literal(f"{field} time span")))

        # Add the time span type
        g.add((ts_node, RDF.type, crm_namespace["E52_Time-Span"]))

    return g


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
        g.add((instance_uri, ns.crm.P1_is_identified_by, apis_id))

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


class PersonCidocSerializer(E21_PersonCidocSerializer):
    def add_life_event_place(self, g, instance, event_type, event_uri):
        if event_type not in ["birth", "death"]:
            raise ValueError("event_type must be one of birth or death")

        rel = None
        if event_type == "birth":
            crm_type = "E67_Birth"
            label_template = "Tod von {}"
            crm_relation = "P98_brought_into_life"
            leg_rel = PersonPlaceLegacyRelation.objects.filter(
                subj_object_id=instance.pk, legacy_relation_vocab_label="geboren in"
            ).first()
            new_rel = WurdeGeborenIn.objects.filter(subj_object_id=instance.pk).first()
            rel = leg_rel or new_rel
        if event_type == "death":
            crm_type = "E69_Death"
            label_template = "Geburt von {}"
            crm_relation = "P100_was_death_of"
            leg_rel = PersonPlaceLegacyRelation.objects.filter(
                subj_object_id=instance.pk, legacy_relation_vocab_label="gestorben in"
            ).first()
            new_rel = StarbIn.objects.filter(subj_object_id=instance.pk).first()
            rel = leg_rel or new_rel

        if not rel:
            return g

        if event_uri is None:
            event_uri = URIRef(ATTRIBUTES[f"{event_type}_{instance.id}"])
            g.add((event_uri, RDF.type, CRM[crm_type]))
            g.add(
                (
                    event_uri,
                    RDFS.label,
                    Literal(label_template.format(str(instance))),
                )
            )
            g.add((event_uri, CRM[crm_relation], self.instance_uri))

        place_ns = Namespace(self.base_uri + rel.obj.get_listview_url())
        g.namespace_manager.bind(rel.obj.get_namespace_prefix(), place_ns)
        place_uri = URIRef(place_ns[str(rel.obj.id)])
        g.add((event_uri, CRM.P7_took_place_at, place_uri))

        return g

    def to_representation(self, instance):
        instance = normalize_empty_attributes(instance)
        g = super().to_representation(instance)

        birth_event = None
        if instance.start is not None:
            birth_event = URIRef(ATTRIBUTES[f"birth_{instance.id}"])
            birth_time_span = URIRef(ATTRIBUTES[f"birth_time-span_{instance.id}"])
            g.add((birth_event, RDF.type, CRM.E67_Birth))
            g.add((birth_event, RDFS.label, Literal(f"Geburt von {str(instance)}")))
            g.add((birth_event, CRM.P98_brought_into_life, self.instance_uri))
            g.add((birth_event, CRM["P4_has_time-span"], birth_time_span))

            birth_time_span = URIRef(ATTRIBUTES[f"birth_time-span_{instance.id}"])
            g = add_time_spans(g, birth_time_span, instance, "start")
        g = self.add_life_event_place(g, instance, "birth", birth_event)

        death_event = None
        if instance.end is not None:
            death_event = URIRef(ATTRIBUTES[f"death_{instance.id}"])
            g.add((death_event, RDFS.label, Literal(f"Tod von {str(instance)}")))
            death_time_span = URIRef(ATTRIBUTES[f"death_time-span_{instance.id}"])
            g.add((death_event, RDF.type, CRM.E69_Death))
            g.add((death_event, CRM.P100_was_death_of, self.instance_uri))
            g.add((death_event, CRM["P4_has_time-span"], death_time_span))

            death_time_span = URIRef(ATTRIBUTES[f"death_time-span_{instance.id}"])
            g = add_time_spans(g, death_time_span, instance, "end")
        g = self.add_life_event_place(g, instance, "death", death_event)
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
        if instance.start is not None:
            joining_time_span_uri = URIRef(
                ns.attr[f"joining_ev_time_span_{instance.id}"]
            )

            g.add((joining_uri, ns.crm["P4_has_time-span"], joining_time_span_uri))
            g = add_time_spans(g, joining_time_span_uri, instance, "start")
        if instance.end is not None:
            leaving_time_span_uri = URIRef(
                ns.attr[f"leaving_ev_time_span_{instance.id}"]
            )
            g.add((leaving_uri, ns.crm["P4_has_time-span"], leaving_time_span_uri))
            g = add_time_spans(g, leaving_time_span_uri, instance, "end")
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
