[![PyPI](https://img.shields.io/pypi/v/django-queryset-feeler.svg?style=flat-square)](https://pypi.python.org/pypi/django-queryset-feeler)
[![Python](https://img.shields.io/pypi/pyversions/django-queryset-feeler.svg?style=flat-square)](https://pypi.python.org/pypi/django-queryset-feeler)
[![Django](https://img.shields.io/badge/django-4.2%20%7C%205.0%20%7C%205.1-blue?style=flat-square)](https://www.djangoproject.com/)

# django-queryset-feeler

Get a better feel for how your django views and serializers are accessing your app's database. Use django-queryset-feeler (dqf) to measure the count, execution time, and raw SQL of your queries from the command line, ipython shell, or jupyter notebook without any configuration.

This extension is used differently than the popular [django-debug-toolbar](https://github.com/jazzband/django-debug-toolbar) in a few ways. First, dqf can be used to profile more than just views. You can pass functions, querysets, model instances, views, class based views, and [django-rest-framework](https://github.com/encode/django-rest-framework/) serializers to dqf for profiling. Second, dqf profiles queries with only one object and can be used in the command line, ipython shell, or jupyter notebook. This is especially useful for prototyping or learning how django querysets are executed.

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

Create a `Feel()` instance by passing it any one of the following objects from your django project. No other configuration is required.

| Query Type | About |
| :--- | :--- |
| `Feel(view)` | Execute a view using an empty HttpRequest. Add a `request` keyword argument to supply your own request. |
| `Feel(ClassBasedView)` | Execute an eligible class based view using an empty HttpRequest with a `GET` method. Add a `request` keyword argument to supply your own request. |
| `Feel(serializer)` | Execute a serializer on the model specified by the serializer's Meta class. |
| `Feel(queryset)` | Execute a queryset |
| `Feel(model_instance)` | Execute a model instance by calling it again from the database using `.refresh_from_db()` |
| `Feel(function)` | Execute a function |

Profile your queries using any of the following properties.

| Property | About |
| :--- | :--- |
| `feel.time` | Repeat the query 32 times (adjust with the `iterations` keyword argument) and return the average query duration in seconds. |
| `feel.count` | Execute the query and return the number of times that the database was accessed. |
| `feel.sql` | Execute the query and return formatted, syntax-highlighted SQL. |
| `feel.tables` | Execute the query and return a dictionary of each table and how many times it was accessed. |
| `feel.report` | Return a human-readable summary of query time, count, and table counts. |
| `feel.queries` | Return a list of individual `Query` objects with `sql`, `time`, and `table` attributes. |
| `feel.to_dict()` | Return structured output for programmatic consumption. |

## Example

The below example illustrates an easy to make django queryset mistake called an 'n + 1 query' and how to use dqf to find it.

#### `project / app / models.py`

```python
class Topping(models.Model):
    name = models.CharField(max_length=100)
    vegetarian = models.BooleanField()

class Pizza(models.Model):
    name = models.CharField(max_length=100)
    toppings = models.ManyToManyField(Topping)
```

#### `project / app / views.py`

```python
def pizza_list(request):
    pizzas = Pizza.objects.all()
    return render(request, 'pizza_list.html', context={'pizzas': pizzas})
```

#### `project / app / templates / app / pizza_list.html`

```html
{% for pizza in pizzas %}
<tr>
    <td>{{ pizza.name }}</td>
    <td>
    {% for topping in pizza.toppings.all %}
        {{ topping.name }}
    {% endfor %}
    </td>
    <td>
    {% with last=pizza.toppings.all|dictsort:'vegetarian'|last %}
        {% if last.vegetarian %}
            🌱
        {% else %}
            🥩
        {% endif %}
    {% endwith %}
    </td>
</tr>
{% endfor %}
```

| Pizza | Toppings | |
| ---: | --- | --- |
| mediterranean | roasted eggplant, balsamic glaze | 🌱 |
| hawaiian | pineapple, smoked ham | 🥩 |
| meat lovers | pepperoni, andouille sausage, capicola | 🥩 |

#### `project / dqf.ipynb`

Note that the `DEBUG` setting in `project / settings.py` must be `True` for dqf to work. `DEBUG` is enabled by default when you create a django project.

```python
from django_queryset_feeler import Feel
from app.views import pizza_list

feel = Feel(pizza_list)

print(f'query count: {feel.count}')
print(f'average duration: {feel.time} s')
print(feel.sql)
```

In the above example django queried the database a total of 4 times: once to get a list of pizzas and then again for each pizza to find its toppings. As more pizzas are added to the menu n + 1 queries would be made to the database where n is the number of pizzas.

Note that even though the pizza's toppings are accessed once in column 2 for the name and again in column 3 to determine if the pizza is vegetarian the database is still accessed only once in this period. This is because after evaluation the results are stored in the queryset object and used for subsequent calls.

A more efficient way to render this template would be to fetch the list of pizzas and then query the toppings table once to get all the toppings for all the pizzas. Django makes this easy using [prefetch_related()](https://docs.djangoproject.com/en/5.1/ref/models/querysets/#prefetch-related).

#### `project / app / views.py`

```python
def pizza_list(request):
    pizzas = Pizza.objects.all().prefetch_related('toppings')
    return render(request, 'pizza_list.html', context={'pizzas': pizzas})
```

#### `project / dqf.ipynb`

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

#### `project / dqf.ipynb`

```python
# re-import modules when a cell is run. This ensures that changes made to
# the django app are synced with your notebook
%load_ext autoreload
%autoreload 2

import django
import os

# change 'project.settings' to '{your_project}.settings'
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()
```
