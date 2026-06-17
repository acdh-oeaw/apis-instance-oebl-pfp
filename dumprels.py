from apis_core.relations.models import Relation
from dataclasses import dataclass
from django.template import Template, Context


@dataclass(unsafe_hash=True)
class RelationType:
    name: str
    subj: object
    obj: object


relation_types = []
parent_types = []

for rel in Relation.objects.all().select_subclasses():
    if hasattr(rel, "subj_model") and hasattr(rel, "obj_model"):
        if not hasattr(rel, "legacy_relation_vocab_label") and rel.subj_model.get_rdf_types() and rel.obj_model.get_rdf_types():
            subj = rel.subj_model
            obj = rel.obj_model
            parent_types.append((subj, obj))
            rel_type = RelationType(rel.name(), subj, obj)
            relation_types.append(rel_type)

parent_types = set(parent_types)
relation_types = set(relation_types)

TMPL = """
@prefix crm: <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix pfps: <https://pfp-schema.acdh.oeaw.ac.at/> .

{% for parent in parent_types %}{% with parent.0.get_verbose_name|lower as subj %}{% with parent.1.get_verbose_name|lower as obj %}
pfps:{{ subj }}-{{ obj }}-relation a owl:Class ;
    rdfs:subClassOf crm:E55_Type ;
    rdfs:label "{{ subj }} {{ obj }} Beziehung"@de ;
    rdfs:label "{{ subj }} {{ obj }} relation"@en ;
    rdfs:domain {{ parent.0.get_rdf_types|first }}
    rdfs:range {{ parent.1.get_rdf_types|first }}
{% endwith %}{% endwith %}{% endfor %}

{% for relation in relation_types %}{% with relation.subj.get_verbose_name|lower as subj %}{% with relation.obj.get_verbose_name|lower as obj %}
pfps:{{ relation.name|slugify}} a pfps:{{ subj }}-{{ obj }}-relation ;
    rdfs:label "{{ relation.name }}"@de ;
{% endwith %}{% endwith %}{% endfor %}
"""


template = Template(TMPL)
context = Context({"relation_types": relation_types, "parent_types": parent_types})
print(template.render(context))
