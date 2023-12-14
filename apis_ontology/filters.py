import logging
import itertools
import re

from django.db import models

PATTERN = re.compile(r'''((?:[^ "']|"[^"]*"|'[^']*')+)''')

logger = logging.getLogger(__name__)


def valuetosearchtype(value):
    if value.strip('"') == value:
        return "__unaccent__icontains", value
    return "__exact", value.strip('"')


def tokenize(value):
    tokens = PATTERN.split(value)
    tokens = list(filter(str.strip, tokens))
    return list(map(valuetosearchtype, tokens))


def name_first_name_filter(queryset, name, value):
    tokens = tokenize(value)
    searchfields = ["first_name", "name"]

    q = models.Q()
    if len(tokens) > 1:
        for combination in itertools.permutations(tokens, len(searchfields)):
            q_and = models.Q()
            mapping = [{field + searchtype: value} for field, (searchtype, value) in zip(searchfields, combination)]
            for query in mapping:
                q_and &= models.Q(**query)
            q |= q_and
    else:
        for searchfield in searchfields:
            mapping = [{searchfield + searchtype: value} for searchtype, value in tokens]
            for query in mapping:
                q |= models.Q(**query)
    logger.debug(q)
    return queryset.filter(q)
