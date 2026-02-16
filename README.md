[![Python](https://img.shields.io/pypi/pyversions/django-queryset-feeler.svg?style=flat-square)](https://pypi.python.org/pypi/django-queryset-feeler)
[![Django](https://img.shields.io/badge/django-4.2%20%7C%205.0%20%7C%205.1%20%7C%205.2-blue?style=flat-square)](https://www.djangoproject.com/)
![Coverage](coverage.svg)

# django-queryset-feeler

Get a feel for how Django queries your database. Profile query count, execution time, and raw SQL from the command line, IPython, or Jupyter. No configuration required.

Unlike [django-debug-toolbar](https://github.com/jazzband/django-debug-toolbar), dqf isn't limited to views. Pass it functions, querysets, model instances, class-based views, or [DRF](https://github.com/encode/django-rest-framework/) serializers. It profiles a single callable and works outside the browser making it useful for prototyping or learning how Django querysets work.

## Installation

```
uv add django-queryset-feeler
```

or with pip:

```
pip install django-queryset-feeler
```

## Usage

```python
from django_queryset_feeler import Feel
```

Pass `Feel()` any of the following:

| Query Type             | About                                                               |
| :--------------------- | :------------------------------------------------------------------ |
| `Feel(view)`           | Profile a function-based view with an empty `HttpRequest`.          |
| `Feel(ClassBasedView)` | Profile a class-based view with an empty `GET` request.             |
| `Feel(serializer)`     | Profile a DRF serializer against all instances of its `Meta.model`. |
| `Feel(queryset)`       | Profile a queryset.                                                 |
| `Feel(model_instance)` | Re-fetch the instance via `.refresh_from_db()`.                     |
| `Feel(function)`       | Profile a plain function.                                           |

Views and CBVs use an empty `HttpRequest` by default. Pass `request=` to supply your own.

Async functions, views, and CBVs are all supported. However, `Feel.profile()` is sync-only; wrap async code blocks in an `async def` instead.

Profile your queries with these properties:

| Property         | About                                                                           |
| :--------------- | :------------------------------------------------------------------------------ |
| `feel.count`     | The number of database queries executed.                                        |
| `feel.time`      | Average execution time in seconds over 32 runs (configurable via `iterations`). |
| `feel.sql`       | Formatted, syntax-highlighted SQL for all queries.                              |
| `feel.tables`    | Dictionary mapping each table to its access count.                              |
| `feel.report`    | Human-readable summary of time, count, and tables.                              |
| `feel.to_dict()` | Machine-readable dict with all query details.                                   |

## Example

This example illustrates an easy-to-make Django queryset mistake called an "n + 1 query" and how to use dqf to find it.

#### `app/models.py`

```python
class Topping(models.Model):
    name = models.CharField(max_length=100)
    vegetarian = models.BooleanField()

class Pizza(models.Model):
    name = models.CharField(max_length=100)
    toppings = models.ManyToManyField(Topping)
```

#### `app/views.py`

```python
def pizza_list(request):
    pizzas = Pizza.objects.all()
    return render(request, 'pizza_list.html', context={'pizzas': pizzas})
```

#### `app/templates/app/pizza_list.html`

```html
{% for pizza in pizzas %}
<tr>
	<td>{{ pizza.name }}</td>
	<td>
		{% for topping in pizza.toppings.all %} {{ topping.name }} {% endfor %}
	</td>
	<td>
		{% with last=pizza.toppings.all|dictsort:'vegetarian'|last %} {% if
		last.vegetarian %} 🌱 {% else %} 🥩 {% endif %} {% endwith %}
	</td>
</tr>
{% endfor %}
```

|         Pizza | Toppings                               |     |
| ------------: | -------------------------------------- | --- |
| mediterranean | roasted eggplant, balsamic glaze       | 🌱  |
|      hawaiian | pineapple, smoked ham                  | 🥩  |
|   meat lovers | pepperoni, andouille sausage, capicola | 🥩  |

#### `dqf.ipynb`

The `DEBUG` setting must be `True` for dqf to work (it's on by default in new Django projects).

```python
from django_queryset_feeler import Feel
from app.views import pizza_list

feel = Feel(pizza_list)

print(f'query count: {feel.count}')
print(f'average duration: {feel.time} s')
print(feel.sql)
```

Django hits the database 4 times: once for the list of pizzas, then once per pizza to get its toppings. As the menu grows, that's n + 1 queries where n is the number of pizzas.

Even though toppings are accessed twice in the template (column 2 for names, column 3 for the vegetarian check), Django only queries once — evaluated results are cached on the queryset.

Fix this with [prefetch_related()](https://docs.djangoproject.com/en/5.1/ref/models/querysets/#prefetch-related), which fetches all toppings in a single extra query:

#### `app/views.py`

```python
def pizza_list(request):
    pizzas = Pizza.objects.all().prefetch_related('toppings')
    return render(request, 'pizza_list.html', context={'pizzas': pizzas})
```

#### `dqf.ipynb`

```python
feel = Feel(pizza_list)
print(feel.report)
```

```
  query count: 2
     duration: 0.069 ms
unique tables: 2
 most accessed: app_pizza (1)
```

## Try it out

Clone the repo and run the demo script to get a shell with sample data pre-loaded:

    git clone https://github.com/lukas-schillinger/django-queryset-feeler.git
    cd django-queryset-feeler
    uv run demo.py

This starts an interactive shell with `Feel`, the example Pizza/Topping models, and sample data ready to go.

## Context Manager

Profile arbitrary code blocks without wrapping them in a function:

```python
with Feel.profile() as f:
    pizzas = Pizza.objects.all()
    for p in pizzas:
        list(p.toppings.all())

print(f.count)    # number of queries
print(f.report)   # full summary
```

## Run Django in a Jupyter Notebook

#### `dqf.ipynb`

```python
# re-import modules when a cell is run. This ensures that changes made to
# the Django app are synced with your notebook
%load_ext autoreload
%autoreload 2

import django
import os

# change 'project.settings' to '{your_project}.settings'
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()
```

**Django 5.2+:** If you're on Django 5.2 or later, `manage.py shell` [auto-imports models](https://docs.djangoproject.com/en/5.2/ref/django-admin/#shell) so you can skip the manual setup above and use dqf directly from the shell.
