# django-reaction

`django-reaction` is an experimental project exploring a server-side-driven architecture for reactive UIs in the Django Admin. The goal is to allow developers to build dynamic admin interfaces—such as conditional field visibility, cascading dropdowns, and dynamic field population—entirely in Python, eliminating the need to write custom frontend JavaScript or HTML.

> **Note**: This project is currently a working prototype and mostly an *idea*. While the provided examples work, the architecture is still evolving. It requires more thought and refactoring (e.g., moving towards a generic AST-based DSL) to become a robust, highly decoupled, and production-ready library.

## How it works: An Example

The core concept relies on mixing `AlpineAdminMixin` with your `ModelAdmin` and defining a set of `reaction_rules`. These rules describe the reactive relationships between your model fields directly in Python. Under the hood, this translates your Python rules into frontend interactions (currently leveraging Alpine.js).

Here is an example of what is already working in the project. You can see the full implementation in [`test_app/admin.py`](test_app/admin.py):

```python
from django.contrib import admin
from django.http import JsonResponse
from django.urls import reverse_lazy

from django_reaction.admin import AlpineAdminMixin
from django_reaction.rule import Rule, Field
from test_app.models import Task, Country, City

@admin.register(Task)
class TaskAdmin(AlpineAdminMixin, admin.ModelAdmin):

    # Define reactive rules for the admin form
    @property
    def reaction_rules(self):
        return [
            # 1. Show the 'params' field only when 'engine' is selected as 'engine_a'
            Rule().when(Field('engine').value == 'engine_a').show(Field('params')),
            
            # 2. Automatically map specific JSON values to 'params' based on the 'engine' selection
            Rule().map_to(Field('params'), Field('engine'), {
                'engine_a': '{"mode": "fast"}',
                'engine_b': '{"mode": "slow"}'
            }),
            
            # 3. Fetch data from a custom endpoint to populate the 'description' based on the 'engine' value
            Rule().fetch(reverse_lazy('admin:myapp_mymodel_custom'), Field('description'), Field('engine')),
            
            # 4. Show the 'description' field only when the 'is_active' checkbox is checked (True)
            Rule().when(Field('is_active').value == True).show(Field('description'))
        ]

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        my_urls = [path(
            'get-engine-config/',
            self.admin_site.admin_view(self.my_custom_view),
            name='myapp_mymodel_custom'
        )]
        return my_urls + urls

    def my_custom_view(self, request):
        return JsonResponse({"1":"2"})

```

With just a few lines of Python, you can declaratively trigger API fetches, map field values, and toggle element visibility based on real-time user input in the Django Admin form.

## Future Architecture

The current implementation successfully demonstrates the concept but leaves room for improvement. The next architectural steps involve replacing the current approach with a highly decoupled, generic AST (Abstract Syntax Tree) DSL. This will separate Triggers, Conditions, and Actions into independent, first-class nodes, making the library significantly more extensible and maintainable for complex use cases.
