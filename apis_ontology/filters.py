import re

from django.contrib.postgres.search import TrigramWordSimilarity
from django.db.models.functions import Greatest

PATTERN = re.compile(r'''((?:[^ "']|"[^"]*"|'[^']*')+)''')


def remove_quotes(token):
    return token.strip('"')


def trigram_search_filter(queryset, name, value):
    tokens = PATTERN.split(value)
    tokens = list(filter(str.strip, tokens))
    tokens = set(list(map(remove_quotes, tokens)) + [value])
    trig_vector_list = []
    for token in tokens:
        trig_vector_list.append(TrigramWordSimilarity(token, "name"))
        trig_vector_list.append(TrigramWordSimilarity(token, "first_name"))
    trig_vector = Greatest(*trig_vector_list)
    return queryset.annotate(similarity=trig_vector).filter(similarity__gt=0.4).order_by("-similarity")
