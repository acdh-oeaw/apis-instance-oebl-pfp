import os
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth.models import Group
from apis_core.apis_entities.signals import post_merge_with

from apis_ontology.models import Text
from apis_highlighter.models import Annotation
from django.contrib.contenttypes.models import ContentType


import logging

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def add_to_group(sender, user, request, **kwargs):
    user_list = os.environ.get("AUTH_LDAP_USER_LIST", "").split(",")
    g1, _ = Group.objects.get_or_create(name='redaktion')
    if user.username in user_list:
        g1.user_set.add(user)


@receiver(post_merge_with)
def merge_texts(sender, instance, entities, **kwargs):
    for entity in entities:
        logger.info(f"Copying texts from {entity} to {instance}")
        content_type = ContentType.objects.get_for_model(entity)
        for text in Text.objects.filter(content_type=content_type, object_id=entity.id):
            text_content_type = ContentType.objects.get_for_model(text)
            if itext := Text.objects.filter(content_type=content_type, object_id=instance.id, kind=text.kind).first():
                # The order of steps here is important
                # We first append to the existing text and only *then*
                # move the pointer of the old annotations to the existing
                # text. If we do it the other way around, the annotation
                # signal would fire and the offsets would be miscalculated
                textlen = len(itext.text + "\n\n")
                itext.text += "\n\n" + text.text
                itext.save()
                for annotation in Annotation.objects.filter(text_content_type=text_content_type, text_object_id=text.id):
                    annotation.start = annotation.start + textlen
                    annotation.end = annotation.end + textlen
                    annotation.text_object_id = itext.id
                    annotation.save()
                text.delete()
            else:
                text.object_id = instance.id
                text.save()
