from django.forms import Script
from collections import defaultdict


class AlpineAdminMixin:
    reaction_rules = []

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        field_attrs = defaultdict(lambda: defaultdict(list))

        for field_name in form.base_fields:
            for rule in self.reaction_rules:
                rule_attrs = rule.get_attrs_for_field(field_name)

                for attr_name, attr_value in rule_attrs.items():
                    if attr_value not in field_attrs[field_name][attr_name]:
                        field_attrs[field_name][attr_name].append(attr_value)

        for field_name, attrs_dict in field_attrs.items():
            if field_name in form.base_fields:
                widget = form.base_fields[field_name].widget

                for attr_name, values in attrs_dict.items():
                    if attr_name == "x-init":
                        widget.attrs[attr_name] = " ".join(values)

                    elif attr_name.startswith("x-model"):
                        widget.attrs[attr_name] = values[0]

                    else:
                        widget.attrs[attr_name] = " ".join(values)

        return form

    class Media:
        js = [
            Script("django_reaction/js/alpine_reaction.js", **dict(defer=True)),
            Script("django_reaction/js/alpinejs@3.14.8.js", **dict(defer=True)),
        ]
