[![This is an image](https://img.shields.io/pypi/v/pyhmer.svg?style=flat-square)](https://pypi.python.org/pypi/django-queryset-feeler)

# django-queryset-feeler

## About
django-queryset-feeler (dqf) is a drop in tool to optimize queryset execution from the command line and notebooks. Get a better feel for how the database is being accessed by native django `views.py` and api `serializers.py`.

## Install
```
$ pip install django-queryset-feeler
```
## Example
### models.py
```python
class Topping(models.Model):
    name = CharField()
    vegan = BooleanField()

class Pizza(models.Model):
    name = CharField()
    toppings = ManyToManyField(Topping)
```
### views.py
```python
def pizza_table(request):
    pizzas = Pizza.objects.all()
    return(request, 'pizza_table.html' context={'pizzas': pizzas})
```
### pizza_table.html
```html
{% for pizza in pizzas %}
<td>
    <tr>{{ pizza.name }}</tr>
    <tr>
        {% for topping in pizza.toppings %}
            {% if topping.vegan %}
                🌱
            {% else %}
                🥩
            {% endif %}
            {{ toppings.name }}
        {% endfor %}
    </tr>
<td>
{% endfor %}
```
### output

| Pizza 	| Toppings 	|  |
| ---: |---	|---
| mediterranean 	| 🌱 roasted eggplant, 🌱 balsamic glaze|
| hawaiian 	|🌱 pineapple, 🥩 smoked ham| 
| meat lovers | 🥩 pepperoni, 🥩 andouille sausage, 🥩 capicola 	|


<br>

## Unoptimized View

<sub>
The below example shows how easy it is to make a mistake formatting django query sets. This view hits the database with a new request for every object in Pizza.objects.all() . 


</sub>

---

<br>

<details>
<summary>
Run django in jupyter notebook
</summary>
<br>

`/project` \
`$ touch dqf.ipynb` 

```python
import django
import os
import django_queryset_visualizer

os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings'
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()
```
---
<br>

</details>

<br>

```python
import django_queryset_feeler as dqf
from app.models import Pizza

def view():
    query = Pizza.objects.all()
    for pizza in query:
        pizza.name
        for topping in pizza.toppings:
            toppings.name
            topping.vegan
            
feel = dqf(view)

print(feel.count_queries())
print(feel.query_time())
print(feel.most_common_table)
print(feel.iterate_queries())
```

>750 database hits\
>800 microsecond query time \
>Topping [app.models.Topping]
>
>
>```sql
>SELECT 'pizza'.'name' FROM 'app_pizza'
>SELECT 'topping' FROM 'app_toppings' where 'ID' = 1\
>SELECT 'topping' FROM 'app_toppings' where 'ID' = 2\
>SELECT 'pizza'.'name' FROM 'app_pizza'
>SELECT 'topping' FROM 'app_toppings' where 'ID' = 1\
>SELECT 'topping' FROM 'app_toppings' where 'ID' = 3\
>...
>```
>
> ### **+_700_ more queries!!!** 
><details>
><summary>
>This is an example of an 'n + 1' query
></summary>
>
>An 'n+ 1' query is
>
>---
><br>
></details>
>

<br>

### **Optimized View**
<sub>
Here .prefetch_related() is used to create a join table between the pizza table and the columns 'name' and 'vegan' from the toppings table.  
</sub>

---

```python
import django_queryset_feeler as dqf
from app.models import Pizza

def view():
    query = Pizza.objects.select_related('toppings')
    for pizza in query:
        pizza.name
        for topping in pizza.toppings:
            toppings.name
            topping.vegan

feel = dqf(view)

print(feel.count_queries)
print(feel.query_time)
print(feel.iterate_queries())
```
> 2 database hits \
> 2 microsecond query time 
>  
>SELECT \
>&nbsp;&nbsp;&nbsp;&nbsp;app_pizza.id, \
>        app_pizza.name, \
>        app_topping.id, \
>        app_topping.name, \
>        app_topping.vegetarian, \
>FROM "app_pizza" 
>
>WHERE ("bubble_phlog"."batch_id" = 'e811'
>       AND "bubble_phlog"."owner_id" = '396') 
>

## Profile Serializers

```python

def is_vegan():
    query = Pizza.objects.all()
    for pizza in query:
        non_vegan = pizza.toppings.filter(vegan=False)
        if non_vegan.exists():
            pizza_vegan = False
        else:
            pizza_vegan = True

```

## output

| Pizza 	| Vegan | Toppings |
| ---: |:---:	|---
| mediterranean | 🌱 | roasted eggplant, balsamic glaze|
| hawaiian 	| 🥩 | pineapple, smoked ham| 
| meat lovers | 🥩 | pepperoni, andouille sausage, capicola 	|
