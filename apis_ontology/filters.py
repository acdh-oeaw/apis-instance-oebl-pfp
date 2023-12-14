from django.db import models


def name_first_name_filter(queryset, name, value):
    return queryset.filter(models.Q(name__unaccent__icontains=value) | models.Q(first_name__unaccent__icontains=value))
