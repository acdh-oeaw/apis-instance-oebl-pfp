import logging
from functools import cache
from typing import Literal

import requests
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

import apis_ontology.models as ontology_models
from apis_core.apis_relations.models import TempTriple
from apis_highlighter.models import Annotation, AnnotationProject

logging.basicConfig(
    filename="relation_creation.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@cache
def fetch_relation_from_api(
    term: str,
    vocab: Literal[
        "personplace",
        "personinstitution",
        "personevent",
        "personwork",
        "personperson",
        "institutionplace",
        "institutionwork",
        "institutionevent",
        "institutioninstitution",
        "eventwork",
        "eventevent",
        "placeevent",
        "placework",
        "placeplace",
        "workwork",
    ],
    field: Literal["name", "name_reverse"] = "name",
):
    if "PIO" in term:
        return None, None
    try:
        term = int(term)
        query = {"id": term, "format": "json"}
    except ValueError:
        query = {field: term, "format": "json"}
    url = f"https://apis.acdh.oeaw.ac.at/apis/api/vocabularies/{vocab}relation/"
    try:
        response = requests.get(url, params=query)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)

        if response.status_code == 200:
            data = response.json()
            if data["count"] == 1:
                label = data["results"][0]["name"]
                label_reverse = data["results"][0]["name_reverse"]
                result = data["results"][0].get("parent_class")
                if result:
                    res_2, res_2_reverse = fetch_relation_from_api(
                        str(result["id"]), vocab, field
                    )
                    label = f"{res_2} >> {label}"
                    label_reverse = f"{res_2_reverse} >> {label_reverse}"
                return label, label_reverse
            else:
                logger.warning(f"got {data['count']} results for query")
        logger.warning(f"no matches found for {term} in vanilla API")
        return None, None  # Return None if no matches found or empty response
    except requests.RequestException as e:
        print(f"Error querying API: {e}")
        logger.error(f"call to vanilla API did not return 200 for {term} to {vocab}")
        return None, None


class Command(BaseCommand):
    help = "Run through existing relations and create ng relation instances from the triples."

    def handle(self, *args, **options):
        classes = [
            cls
            for name, cls in ontology_models.__dict__.items()
            if isinstance(cls, type)
        ]
        ann_projects_new = dict()
        relation_class_names = [cls.__name__ for cls in classes]
        relation_classes = {
            cls._legacy_property_id: cls
            for cls in classes
            if hasattr(cls, "_legacy_property_id")
        }
        triple_content_type = ContentType.objects.get_for_model(TempTriple)
        for temptriple in TempTriple.objects.all().order_by("prop"):
            attributes = {
                field.name: getattr(temptriple, field.name)
                for field in TempTriple._meta.fields
                if field.name not in ["prop", "id", "pk", "triple_ptr"]
            }
            if temptriple.prop_id in relation_classes:
                rel_class = relation_classes[temptriple.prop_id]
            else:
                opt_a = f"{temptriple.subj.__class__.__name__.title()}{temptriple.obj.__class__.__name__.title()}"
                opt_b = f"{temptriple.obj.__class__.__name__.title()}{temptriple.subj.__class__.__name__.title()}"
                if f"{opt_a}LegacyRelation" in relation_class_names:
                    rel_class = getattr(ontology_models, f"{opt_a}LegacyRelation")
                    vocab = opt_a.lower()
                    field = "name"
                elif f"{opt_b}LegacyRelation" in relation_class_names:
                    rel_class = getattr(ontology_models, f"{opt_b}LegacyRelation")
                    vocab = opt_b.lower()
                    field = "name_reverse"
                else:
                    logger.warning(f"couldnt find class to use for {opt_a} / {opt_b}")
                    continue
                vocab_label_vanilla, vocab_label_vanilla_reverse = (
                    fetch_relation_from_api(temptriple.prop.name_forward, vocab, field)
                )
                attributes["legacy_relation_vocab_label"] = vocab_label_vanilla
                attributes["legacy_relation_vocab_label_reverse"] = (
                    vocab_label_vanilla_reverse
                )
            new_rel = rel_class.objects.create(**attributes)
            for ann in Annotation.objects.filter(
                content_type=triple_content_type, object_id=temptriple.id
            ):
                if ann.project_id in ann_projects_new:
                    ann_proj = ann_projects_new[ann.project_id]
                else:
                    ann_proj = AnnotationProject.objects.create(
                        name=f"{ann.project.name}-ng"
                    )
                    ann_projects_new[ann.project_id] = ann_proj
                # Create new annotation by copying the old one
                ann_new = Annotation()
                ann_new.__dict__.update(ann.__dict__)

                # Clear primary key and specific fields
                ann_new.pk = None
                ann_new.id = None
                ann_new.content_object = new_rel
                ann_new.project = ann_proj

                # Save the new instance
                ann_new.save()
