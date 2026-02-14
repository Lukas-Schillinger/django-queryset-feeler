"""Interactive demo shell with sample data pre-loaded."""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

import django

django.setup()

from django.core.management import call_command

call_command("migrate", "--run-syncdb", verbosity=0)

from django_queryset_feeler import Feel
from tests.models import Pizza, Topping
from tests.test_feel import create_models
from tests.views import pizza_list_optimized, pizza_list_unoptimized

create_models()

feel = Feel(pizza_list_unoptimized)

banner = """
django-queryset-feeler demo
============================

Available objects:
  feel    — Feel(pizza_list_unoptimized)  (try feel.count, feel.sql, feel.report)
  Feel    — create your own: Feel(pizza_list_optimized), Feel(Pizza.objects.all()), ...
  Pizza, Topping — test models (3 pizzas, 7 toppings seeded)
  pizza_list_unoptimized, pizza_list_optimized — example views
"""

namespace = {
    "Feel": Feel,
    "Pizza": Pizza,
    "Topping": Topping,
    "pizza_list_unoptimized": pizza_list_unoptimized,
    "pizza_list_optimized": pizza_list_optimized,
    "feel": feel,
}

print(banner)

try:
    from IPython import start_ipython

    start_ipython(argv=[], user_ns=namespace)
except ImportError:
    import code

    code.interact(local=namespace, banner="")

sys.exit()
