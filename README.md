[![This is an image](https://img.shields.io/pypi/v/django-queryset-feeler.svg?style=flat-square)](https://pypi.python.org/pypi/django-queryset-feeler)

# django-queryset-feeler

Get a better feel for how your django views and serializers are accessing your app’s database. Use django-queryset-feeler (dqf) to measure the count, execution time, and raw SQL of your queries from the command line, ipython shell, or jupyter notebook without any configuration.

This extension is used differently than the popular [django-debug-toolbar](https://github.com/jazzband/django-debug-toolbar) in a few ways. First, dqf can be used to profile more than just views. You can pass functions, querysets, views, class based views, and [django-rest-framework](https://github.com/encode/django-rest-framework/) serializers to dqf for profiling. Second, dqf profiles queries with only one object and can be used in the command line, ipython shell, or jupyter notebook. This is especially useful for prototyping or learning how django querysets are executed. 

## Usage
```
pip install django-queryset-feeler
```
```python
from django_queryset_feeler import Feel
```
| Query Type | About |
| :--- | :--- |
| `Feel(view)`| Execute a view using an empty HttpRequest. Add a `request` key word argument to supply your own request. | 
| `Feel(ClassBasedView)` | Execute an eligible class based view using an empty HttpRequest with a `GET` method. Add a `request` key word argument to supply your own request. |
| `Feel(serializer)` | Execute a serializer on the model specified by the serializer's Meta class. |
| `Feel(queryset)` | Execute a queryset |
| `Feel(function)` | Execute a function |


| Property | About 
| :--- | :---
| `feel.query_time`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  | Repeat the query 100 times (adjust iterations with the `iterations` key word argument) and return the average query duration in seconds.  
| `feel.query_count` | Execute the query and return the number of times that the database was accessed. 
| `feel.sql_queries` | Execute the query and return a formatted copy of the raw SQL. 
| `feel.table_counts` | Execute the query and return a dictionary containing each table and how many times it was accessed. 
|`feel.report` | Print the query time, count, and table count summary.  

## Example
The below example illustrates an easy to make django queryset mistake called an 'n + 1' query and how to use dqf to find it.   
#### `project / app / models.py`
```python
class Topping(models.Model):
    name = CharField()
    vegetarian = BooleanField()

class Pizza(models.Model):
    name = CharField()
    toppings = ManyToManyField(Topping)
```
#### `project / app / views.py`
```python
def pizza_list(request):
    pizzas = Pizza.objects.all()
    return(request, 'pizza_list.html' context={'pizzas': pizzas})
```
#### `project / app / templates / app / pizza_list.html`
```html
{% for pizza in pizzas %}
<td>
    <tr>{{ pizza.name }}</tr>
    <tr>
    {% for topping in pizza.toppings %}
        {{ topping.name }}
    {% endfor %}
    </tr>
    <tr>
    {% with last=pizza.toppings|dictsort:'vegetarian'|last %}
        {% if last.vegetarian %}
            🌱
        {% else %}
            🥩
        {% endif %}
    {% endwith %}
    </tr>
<td>
{% endfor %}
```

| Pizza | Toppings | |
| ---: | --- | ---
| mediterranean | roasted eggplant, balsamic glaze | 🌱
| hawaiian | pineapple, smoked ham | 🥩
| meat lovers | pepperoni, andouille sausage, capicola | 🥩


#### `project / dqf.ipynb`
Note that the `DEBUG` setting in `project / settings.py` must be `True` for dqf to work. `DEBUG` is enabled by default when you create a django project. 
```python
from django_queryset_feeler import Feel
from app.views import pizza_list

feel = Feel(pizza_list)

print(f'query count: {feel.query_count}')
print(f'average duration: {feel.duration} s')
print(feel.sql_queries)
```

```python
'query count: 4'
'average duration: 0.00023 s'

SELECT "app_pizza"."id",
       "app_pizza"."name",
FROM "app_pizza"

SELECT "app_topping"."id",
       "app_topping"."name",
       "app_topping"."vegetarian"
FROM "app_topping"
WHERE "app_topping"."id" = '0'

SELECT "app_topping"."id",
       "app_topping"."name",
       "app_topping"."vegetarian"
FROM "app_topping"
WHERE "app_topping"."id" = '1'

SELECT "app_topping"."id",
       "app_topping"."name",
       "app_topping"."vegetarian"
FROM "app_topping"
WHERE "app_topping"."id" = '2'
```
In the above example django queried the database a total of 4 times: once to get a list of pizzas and then again for each pizza to find its toppings. As more pizzas are added to the menu n + 1 queries would be made to the database where n is the number of pizzas. 

Note that even though the pizza's toppings are accessed once in column 2 for the name and again in column 3 to determine if the pizza is vegetarian the database is still accessed only once in this period. This is because after evaluation the results are stored in the queryset object and used for subsequent calls. 

A more efficient way to render this template would be to fetch the list of pizzas and then query the toppings table once to get all the toppings for all the pizzas. Django makes this easy using [prefetch_related()](https://docs.djangoproject.com/en/4.0/ref/models/querysets/#prefetch-related). 
#### `project / app / views.py` 
```python
def pizza_list(request):
    pizzas = Pizza.objects.all().prefetch_related('toppings')
    return(request, 'pizza_list.html' context={'pizzas': pizzas})
```
#### `project / dqf.ipynb`
```python
feel = Feel(pizza_list)
feel.report
```
```python
     query count: 2         
average duration: 0.069 ms                
   unique tables: 2         
        accessed   
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

# change 'project.settings' to '{ your project }.settings'
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()
```
