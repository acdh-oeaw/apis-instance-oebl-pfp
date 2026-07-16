from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apis_core.relations.models import Relation

# ListRelationTypesAPIView API endpoint:
#
# The endpoint was created according to this schema example:
# ```
# "relations": {
#   "arbeitetezusammenmit": {
#     "model": "apis_ontology.arbeitetezusammenmit",
#     "class_name": "ArbeiteteZusammenMit",
#     "name": "arbeitete zusammen mit [PIO]",
#     "reverse_name": "arbeitete zusammen mit [PIO]",
#     "subj_model": [
#       "Person"
#     ],
#     "obj_model": [
#       "Person"
#     ],
#     "legacy_property_id": null,
#   },
#   "dissertiertebeiunter": {
#     "model": "apis_ontology.dissertiertebeiunter",
#     "class_name": "DissertierteBeiunter",
#     "name": "dissertierte bei/unter [PIO]",
#     "reverse_name": "war Doktorvater von [PIO]",
#     "subj_model": [
#       "Person"
#     ],
#     "obj_model": [
#       "Person"
#     ],
#     "legacy_property_id": 167032,
#   },
# ```
# The `subj_model` and `obj_model` where changed to be single values,
# because apis-core-rdf does not allow lists, so it does not make
# sense to serialize those values as lists.


class ListRelationTypesAPIView(APIView):
    """
    Custom temporary endpoint for "AI Experiments" project
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        relation_classes = list(
            filter(lambda x: issubclass(x, Relation), apps.get_models())
        )
        relation_classes = list(filter(lambda x: x != Relation, relation_classes))
        relations = {}
        for cls in relation_classes:
            content_type = ContentType.objects.get_for_model(cls)
            relations[content_type.model] = {
                "model": f"{content_type.app_label}.{content_type.model}",
                "class_name": cls.__name__,
                "name": cls.name(),
                "reverse_name": cls.reverse_name(),
                "subj_model": cls.subj_model.__name__,
                "obj_model": cls.obj_model.__name__,
                "legacy_property_id": getattr(cls, "_legacy_property_id", None),
            }

        return Response({"relations": relations})
