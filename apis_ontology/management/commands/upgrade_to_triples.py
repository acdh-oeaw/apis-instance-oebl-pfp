import os
from django.core.management.base import BaseCommand
from django.db.models.query import QuerySet
from django.conf import settings

from apis_core.apis_relations.models import Property, Triple


def to_camel_case(value):
    characters_replace = [
        ("ä", "ae"),
        ("ö", "oe"),
        ("ü", "ue"),
        ("ß", "ss"),
        ("á", "a"),
        ("é", "e"),
        ("í", "i"),
        ("ó", "o"),
        ("ú", "u"),
        ("à", "a"),
        ("è", "e"),
        ("ì", "i"),
        ("ò", "o"),
        ("ù", "u"),
        ("â", "a"),
        ("ê", "e"),
        ("î", "i"),
        ("ô", "o"),
        ("û", "u"),
        ("ñ", "n"),
        ("ç", "c"),
        (".", ""),
        ("-", ""),
        ("_", ""),
        ("/", ""),
        ("(", ""),
        (")", ""),
        ("'", ""),
        ("&", ""),
        (",", ""),
        ("[", "_"),
        ("]", ""),
        (":", ""),
    ]
    for character in characters_replace:
        value = value.replace(character[0], character[1])
    content = "".join(value.title().split())
    return content


def format_classes(value):
    if isinstance(value, QuerySet):
        if value.count() == 1:
            return value.first().model_class().__name__
        return (
            "["
            + ", ".join(
                [cls for cls in (format_classes(v) for v in value) if cls is not None]
            )
            + "]"
        )
    else:
        omit_classes = ["Property"]
        if value.model_class().__name__ in omit_classes:
            return None
        return value.model_class().__name__


template_generic_relation = """
class TempTripleGenericAttributes(models.Model):
    \"\"\"
    This class is used to store legacy attributes from the old triple model.
    It is used to store the attributes that are not part of the new relations model.
    \"\"\"

    class Meta:
        abstract = True

    review = models.BooleanField(
        default=False,
        help_text="Should be set to True, if the data record holds up quality standards.",
    )
    status = models.CharField(max_length=100, blank=True, null=True)
    references = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
"""

template_legacy_relation = """
class TempTripleLegacyAttributes(models.Model):
    \"\"\"
    Adds common attributes of the legact relation classes
    \"\"\"

    class Meta:
        abstract = True

    legacy_relation_vocab_label = models.CharField(max_length=255, blank=True, null=True)
    legacy_relation_vocab_label_reverse = models.CharField(max_length=255, blank=True, null=True)

    def name(self) -> str:
        return self.legacy_relation_vocab_label

    def reverse_name(self) -> str:
        return self.legacy_relation_vocab_label_reverse

"""

template = """
class {relation_class}(Relation{additional_base_classes}, TempTripleGenericAttributes, LegacyDateMixin):
    \"\"\"automatically generated class from property with id {prop_id}\"\"\"

    _legacy_property_id = {prop_id}

    subj_model = {subj_model}
    obj_model = {obj_model}


    @classmethod
    def name(self) -> str:
        return "{relation_label}"

    @classmethod
    def reverse_name(self) -> str:
        return "{reverse_relation_label}"
"""

template_legacy = """
class {relation_class}LegacyRelation(Relation{additional_base_classes}, TempTripleGenericAttributes, TempTripleLegacyAttributes, LegacyDateMixin):
    \"\"\"automatically generated class\"\"\"

    subj_model = {subj_model}
    obj_model = {obj_model}

    @classmethod
    def name(self) -> str:
        return "{relation_class}"

    @classmethod
    def reverse_name(self) -> str:
        return "{relation_class} reverse"
"""


def handle_pio_relations(cls_name, cls_names, classes, prop):
    cls_names.append(cls_name)
    classes.append(
        template.format(
            relation_class=cls_name.replace("_Pio", ""),
            additional_base_classes=", VersionMixin"
            if "apis_core.history" in settings.INSTALLED_APPS
            else "",
            prop_id=prop.id,
            subj_model=format_classes(prop.subj_class.all()),
            obj_model=format_classes(prop.obj_class.all()),
            relation_label=prop.name_forward,
            reverse_relation_label=prop.name_reverse,
        )
    )
    return cls_names, classes


def split_camel_case(term: str) -> list[str]:
    for idx, letter in enumerate(term):
        if letter.isupper() and idx > 1:
            return (term[0:idx], term[idx:])


def handle_legacy_relations(cls_name, cls_names, classes, prop):
    subj_models = [ct.model for ct in prop.subj_class.all()]
    obj_models = [ct.model for ct in prop.obj_class.all()]

    allowed_vocabs = [
        "PersonPlace",
        "PersonInstitution",
        "PersonEvent",
        "PersonWork",
        "PersonPerson",
        "InstitutionPlace",
        "InstitutionWork",
        "InstitutionEvent",
        "InstitutionInstitution",
        "EventWork",
        "EventEvent",
        "PlaceEvent",
        "PlaceWork",
        "PlacePlace",
        "WorkWork",
    ]

    valid_combinations = []
    for subj in subj_models:
        for obj in obj_models:
            combo = f"{subj.title()}{obj.title()}"
            combo_reverse = f"{obj.title()}{subj.title()}"
            if combo in allowed_vocabs:
                valid_combinations.append(
                    (combo, f"{subj.title()} {obj.title()} Relation")
                )
            if combo_reverse in allowed_vocabs:
                valid_combinations.append(
                    (combo_reverse, f"{obj.title()} {subj.title()} Relation")
                )

    if valid_combinations:
        for comb, comb_label in valid_combinations:
            cls_pre = template_legacy.format(
                relation_class=comb,
                additional_base_classes=", VersionMixin"
                if "apis_core.history" in settings.INSTALLED_APPS
                else "",
                subj_model=split_camel_case(comb)[0].lower().title(),
                obj_model=split_camel_case(comb)[1].lower().title(),
                relation_label=comb_label,
                reverse_relation_label=f"{comb_label} (reverse)",
            )
            if cls_pre not in classes:
                classes.append(cls_pre)
    #            js_val = fetch_relation_from_api(
    #                prop.name_forward if check_combo else prop.name_reverse, comb
    #            )
    #            pass
    else:
        print("no valid combinations")
    return cls_names, classes


class Command(BaseCommand):
    help = "Run through existing relations and create ng relation classes from the properties."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file", type=str, help="File to write the new relation classes to."
        )
        parser.add_argument(
            "--auto_format",
            action="store_true",
            help="Whether to auto format the file using ruff (dependency needs to be available).",
        )

    def handle(self, *args, **options):
        classes = []
        cls_names = []
        for prop in Property.objects.all():
            obj_subj_class_names = set(
                [ct.model for ct in prop.subj_class.all()]
                + [ct.model for ct in prop.obj_class.all()]
            )
            cls_name = to_camel_case(prop.name_forward)
            if cls_name in cls_names:
                if cls_name[-1].isdigit():
                    cls_name = cls_name[:-1] + str(int(cls_name[-1]) + 1)
                else:
                    cls_name += "1"
            if Triple.objects.filter(prop=prop).count() == 0:
                continue
            if "PIO" in prop.name_forward or "denomination" in obj_subj_class_names:
                cls_names, classes = handle_pio_relations(
                    cls_name, cls_names, classes, prop
                )
            else:
                cls_names, classes = handle_legacy_relations(
                    cls_name, cls_names, classes, prop
                )
        if options["file"]:
            with open(options["file"], "r") as of:
                with open(options["file"] + ".tmp", "w") as f:
                    f.write("from apis_core.relations.models import Relation\n")
                    f.write(of.read())
                    f.write("\n\n")
                    f.write(template_generic_relation)
                    f.write("\n\n")
                    f.write(template_legacy_relation)
                    f.write(
                        "\n################################################\n#auto generated relation classes from properties\n################################################\n"
                    )
                    f.write("\n\n".join(classes))
                    f.seek(0)
            os.remove(options["file"])
            os.rename(options["file"] + ".tmp", options["file"])
            if options["auto_format"]:
                try:
                    import ruff

                    ruff.format_file(options["file"])
                    ruff.isort_file(options["file"])
                except ImportError:
                    print(
                        "Auto formatting not possible, ruff not available. Please install ruff."
                    )
