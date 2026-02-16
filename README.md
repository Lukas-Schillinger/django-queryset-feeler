[![PyPI](https://img.shields.io/pypi/v/django-queryset-feeler.svg?style=flat-square)](https://pypi.python.org/pypi/django-queryset-feeler)
[![Python](https://img.shields.io/pypi/pyversions/django-queryset-feeler.svg?style=flat-square)](https://pypi.python.org/pypi/django-queryset-feeler)
[![Django](https://img.shields.io/badge/django-4.2%20%7C%205.0%20%7C%205.1%20%7C%205.2-blue?style=flat-square)](https://www.djangoproject.com/)

# django-queryset-feeler

Get a feel for how Django queries your databse. Measure the count, execution time, and raw SQL of ORM queries from the command line, ipython shell, or jupyter notebook. No configuration required.

Unlike [django-debug-toolbar](https://github.com/jazzband/django-debug-toolbar), dqf isn't limited to views. Pass it functions, querysets, model instances, class based views, or [DRF](https://github.com/encode/django-rest-framework/) serializers. It profiles with a single object and works outside the browser, making it great for prototyping or learning how django querysets behave.

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

| Query Type             | About                                                                                                                                             |
| :--------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------ |
| `Feel(view)`           | Execute a view using an empty HttpRequest. Add a `request` keyword argument to supply your own request.                                           |
| `Feel(ClassBasedView)` | Execute an eligible class based view using an empty HttpRequest with a `GET` method. Add a `request` keyword argument to supply your own request. |
| `Feel(serializer)`     | Execute a serializer on the model specified by the serializer's Meta class.                                                                       |
| `Feel(queryset)`       | Execute a queryset                                                                                                                                |
| `Feel(model_instance)` | Execute a model instance by calling it again from the database using `.refresh_from_db()`                                                         |
| `Feel(function)`       | Execute a function                                                                                                                                |

Profile your queries using any of the following properties.

| Property         | About                                                                                                                       |
| :--------------- | :-------------------------------------------------------------------------------------------------------------------------- |
| `feel.time`      | Repeat the query 32 times (adjust with the `iterations` keyword argument) and return the average query duration in seconds. |
| `feel.count`     | Execute the query and return the number of times that the database was accessed.                                            |
| `feel.sql`       | Execute the query and return formatted, syntax-highlighted SQL.                                                             |
| `feel.tables`    | Execute the query and return a dictionary of each table and how many times it was accessed.                                 |
| `feel.report`    | Return a human-readable summary of query time, count, and table counts.                                                     |
| `feel.to_dict()` | Return structured output for programmatic consumption including individual query details.                                   |

## Example

The below example illustrates an easy to make django queryset mistake called an 'n + 1 query' and how to use dqf to find it.

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

The `DEBUG` setting must be `True` for dqf to work (it's on by default in new django projects).

```python
from django_queryset_feeler import Feel
from app.views import pizza_list

feel = Feel(pizza_list)

print(f'query count: {feel.count}')
print(f'average duration: {feel.time} s')
print(feel.sql)
```

Django hit the database 4 times: once for the list of pizzas, then once per pizza to get its toppings. As the menu grows, that's n + 1 queries where n is the number of pizzas.

Even though toppings are accessed twice in the template (column 2 for names, column 3 for the vegetarian check), django only queries once — evaluated results are cached on the queryset.

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

**Django 5.2+:** If you're on Django 5.2 or later, `manage.py shell` [auto-imports models](https://docs.djangoproject.com/en/5.2/ref/django-admin/#shell) so you can skip the manual setup above and use dqf directly from the shell.
