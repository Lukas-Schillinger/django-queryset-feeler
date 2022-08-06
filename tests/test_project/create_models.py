from test_app.models import Pizza, Topping

Pizza.objects.all().delete()
Topping.objects.all().delete()

toppings = Topping.objects.bulk_create([
    Topping(name='roasted eggplant', vegetarian=True),
    Topping(name='balsamic glaze', vegetarian=True), 
    Topping(name='pineapple', vegetarian=True), 
    Topping(name='smoked ham', vegetarian=False), 
    Topping(name='pepperoni', vegetarian=False), 
    Topping(name='andouille sausage', vegetarian=False), 
    Topping(name='capicola', vegetarian=False), 
])


mediterranean = Pizza(name='Mediterranean')
hawaiian = Pizza(name='Hawaiian')
meat_lovers = Pizza(name='Meat Lovers')

mediterranean.save()
hawaiian.save()
meat_lovers.save()

mediterranean.toppings.add(Topping.objects.get(name='roasted eggplant'))
mediterranean.toppings.add(Topping.objects.get(name='balsamic glaze'))

hawaiian.toppings.add(Topping.objects.get(name='pineapple'))
hawaiian.toppings.add(Topping.objects.get(name='smoked ham'))

meat_lovers.toppings.add(Topping.objects.get(name='pepperoni'))
meat_lovers.toppings.add(Topping.objects.get(name='capicola'))
meat_lovers.toppings.add(Topping.objects.get(name='andouille sausage'))

