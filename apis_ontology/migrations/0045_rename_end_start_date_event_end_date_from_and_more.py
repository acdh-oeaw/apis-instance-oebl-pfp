# Generated by Django 5.1.4 on 2024-12-20 07:33

import django_interval.fields
from django.db import migrations

migration_list = lambda model: [  # noqa: E731
    migrations.RenameField(
        model_name=model,
        old_name="end_date_written",
        new_name="end",
    ),
    migrations.RenameField(
        model_name=model,
        old_name="end_start_date",
        new_name="end_date_from",
    ),
    migrations.RenameField(
        model_name=model,
        old_name="end_date",
        new_name="end_date_sort",
    ),
    migrations.RenameField(
        model_name=model,
        old_name="end_end_date",
        new_name="end_date_to",
    ),
    migrations.RenameField(
        model_name=model,
        old_name="start_date_written",
        new_name="start",
    ),
    migrations.RenameField(
        model_name=model,
        old_name="start_start_date",
        new_name="start_date_from",
    ),
    migrations.RenameField(
        model_name=model,
        old_name="start_date",
        new_name="start_date_sort",
    ),
    migrations.RenameField(
        model_name=model,
        old_name="start_end_date",
        new_name="start_date_to",
    ),
    migrations.AlterField(
        model_name=model,
        name="start",
        field=django_interval.fields.FuzzyDateParserField(
            blank=True, max_length=255, null=True, verbose_name="Start"
        ),
    ),
    migrations.AlterField(
        model_name=model,
        name="end",
        field=django_interval.fields.FuzzyDateParserField(
            blank=True, max_length=255, null=True, verbose_name="End"
        ),
    ),
]
entities = ["event", "institution", "person", "place", "work"]
relations = [
    "hatreligionszugehoerigkeit",
    "personeventlegacyrelation",
    "personinstitutionlegacyrelation",
    "personpersonlegacyrelation",
    "institutioninstitutionlegacyrelation",
    "personplacelegacyrelation",
    "personworklegacyrelation",
    "placeplacelegacyrelation",
    "wargeschwistervon",
    "warschwagerschwaegerinvon",
    "warschwiegersohnschwiegertochtervon",
    "warverwandtmit",
    "hattealstrauzeugenzeugin",
    "warpatenkindvon",
    "dissertiertebeiunter",
    "wurdegeborenin",
    "starbin",
    "erhieltausbildungin",
    "wirkteforschtehieltsichaufin",
    "studiertelerntean",
    "habilitiertesichan",
    "warassistentinan",
    "warprivatdozentinan",
    "warotitoprofessorinan",
    "waraotitaoprofessorinan",
    "warhonorarprofessorinan",
    "warehrendoktorinan",
    "wartaetigfuerwirkteanbei",
    "warmitgruenderinvon",
    "hatteleitungsfunktionan",
    "warmitgliedvon",
    "wargrossvatermuttervon",
    "warrektorinan",
    "wardekaninan",
    "promoviertean",
    "kaempfteinbei",
    "warprofessorinan",
    "graduiertean",
    "mitbiographiertunter",
    "warhonorardozentinan",
    "hatteleitungsfunktionbei",
    "nahmteilan",
    "warelternteilvon",
    "warschuelerinvon",
    "warverheiratetmit",
    "standinkontaktmit",
    "arbeitetezusammenmit",
    "wurdeerhobenin",
    "wargeburtstitelvon",
    "fandstattin",
]
allmodels = (
    entities
    + relations
    + [f"version{entity}" for entity in entities]
    + [f"version{relation}" for relation in relations]
)


class Migration(migrations.Migration):
    dependencies = [
        ("apis_ontology", "0044_person_alternative_names_new_and_more"),
    ]

    operations = [item for model in allmodels for item in migration_list(model)]