import os
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth.models import Group



@receiver(user_logged_in)
def add_to_group(sender, user, request, **kwargs):
    user_list = os.environ.get("AUTH_LDAP_USER_LIST", "").split(",")
    g1, _ = Group.objects.get_or_create(name='redaktion')
    if user.username in user_list:
        g1.user_set.add(user)
