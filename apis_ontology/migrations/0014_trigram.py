# Generated by Django 4.2.8 on 2024-01-19 09:31

from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("apis_ontology", "0012_professioncategory_alter_profession_options_and_more"),
    ]

    operations = [TrigramExtension()]
