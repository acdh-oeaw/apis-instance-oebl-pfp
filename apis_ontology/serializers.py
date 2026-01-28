from typing import Any

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD

from apis_core.apis_entities.serializers import E21_PersonCidocSerializer
from apis_core.generic.serializers import GenericModelCidocSerializer
from apis_core.generic.utils.rdf_namespace import ATTRIBUTES, CRM
from apis_core.relations.utils import relation_content_types
from apis_ontology.models import (
    Institution,
    Person,
    PersonPlaceLegacyRelation,
    PersonWorkLegacyRelation,
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

        place_ns = Namespace(rel.obj.get_namespace_uri())
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
            if instance.start_date_sort or (
                instance.start_date_from and instance.start_date_to
            ):
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
            if instance.end_date_sort or (
                instance.end_date_from and instance.end_date_to
            ):
                g.add((death_event, CRM["P4_has_time-span"], death_time_span))
                death_time_span = URIRef(ATTRIBUTES[f"death_time-span_{instance.id}"])
                g = add_time_spans(g, death_time_span, instance, "end")
        g = self.add_life_event_place(g, instance, "death", death_event)
        return g


class PersonInstitutionCidocBaseSerializer(GenericModelCidocSerializer):
    def to_representation(self, instance):
        instance = normalize_empty_attributes(instance)
        g = super().to_representation(instance)

        person = (
            instance.obj
            if instance.obj_content_type.model == "person"
            else instance.subj
        )
        # Create the Person instance
        person_ns = Namespace(person.get_namespace_uri())
        g.namespace_manager.bind(person.get_namespace_prefix(), person_ns)
        person_uri = URIRef(person_ns[str(person.id)])
        g.add(
            (person_uri, RDF.type, CRM.E21_Person)
        )  # maybe remove that as also in detail view of person
        institution = (
            instance.subj if instance.subj_object_id != person.id else instance.obj
        )
        institution_ns = Namespace(institution.get_namespace_uri())
        g.namespace_manager.bind(institution.get_namespace_prefix(), institution_ns)
        inst_uri = URIRef(institution_ns[str(institution.id)])
        g.add((inst_uri, RDF.type, CRM.E74_Group))

        joining_uri = URIRef(ATTRIBUTES[f"joining_ev_{instance.id}"])
        g.add((joining_uri, RDF.type, CRM.E85_Joining))
        g.add((joining_uri, RDFS.label, Literal(f"{str(instance)} gestartet")))
        pc_joining_uri = URIRef(ATTRIBUTES[f"pc_joining_ev_{instance.id}"])
        memb_type_uri = URIRef(ATTRIBUTES[f"kind_member_{instance.id}"])
        g.add((person_uri, CRM.P143i_was_joined_by, joining_uri))
        g.add((joining_uri, CRM.P01i_is_domain_of, pc_joining_uri))
        g.add((pc_joining_uri, CRM.P02_has_range, inst_uri))
        g.add((pc_joining_uri, RDF.type, CRM["PC144_joined_with"]))
        g.add((pc_joining_uri, CRM.P144_1_kind_of_member, memb_type_uri))
        g.add((memb_type_uri, RDFS.label, Literal(instance.name())))
        g.add((memb_type_uri, RDF.type, CRM.E55_Type))
        leaving_uri = URIRef(ATTRIBUTES[f"leaving_ev_{instance.id}"])
        g.add((leaving_uri, RDF.type, CRM.E86_Leaving))
        g.add((person_uri, CRM["P145i_left_by"], leaving_uri))
        g.add((leaving_uri, CRM["P146_separated_from"], inst_uri))
        g.add((leaving_uri, RDFS.label, Literal(f"{str(instance)} beendet")))
        if instance.start is not None:
            joining_time_span_uri = URIRef(
                ATTRIBUTES[f"joining_ev_time_span_{instance.id}"]
            )

            g.add((joining_uri, CRM["P4_has_time-span"], joining_time_span_uri))
            g = add_time_spans(g, joining_time_span_uri, instance, "start")
        if instance.end is not None:
            leaving_time_span_uri = URIRef(
                ATTRIBUTES[f"leaving_ev_time_span_{instance.id}"]
            )
            g.add((leaving_uri, CRM["P4_has_time-span"], leaving_time_span_uri))
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


class WorkCidocSerializer(GenericModelCidocSerializer):
    """
    Extend the existing serializer to add the `P67_refers_to` relation to the work cidoc export
    """

    def to_representation(self, instance):
        g = super().to_representation(instance)

        for relation in PersonWorkLegacyRelation.objects.filter(
            obj_content_type=instance.content_type, obj_object_id=instance.id
        ):
            person = relation.subj
            person_ns = Namespace(person.get_namespace_uri())
            g.namespace_manager.bind(person.get_namespace_prefix(), person_ns)
            person_uri = URIRef(person_ns[str(person.id)])
            g.add((self.appellation_uri, CRM["P67_refers_to"], person_uri))
        return g
