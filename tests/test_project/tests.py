from django_queryset_feeler import Feel

from django.test import TestCase
from django.conf import settings

from test_app.models import Pizza, Topping
from test_app.serializers import PizzaSerializer, ToppingSerializer
from test_app import views

settings.DEBUG = True


def create_models():
    Topping.objects.bulk_create(
        [
            Topping(name="roasted eggplant", vegetarian=True),
            Topping(name="balsamic glaze", vegetarian=True),
            Topping(name="pineapple", vegetarian=True),
            Topping(name="smoked ham", vegetarian=False),
            Topping(name="pepperoni", vegetarian=False),
            Topping(name="andouille sausage", vegetarian=False),
            Topping(name="capicola", vegetarian=False),
        ]
    )

    mediterranean = Pizza(name="Mediterranean")
    hawaiian = Pizza(name="Hawaiian")
    meat_lovers = Pizza(name="Meat Lovers")

    mediterranean.save()
    hawaiian.save()
    meat_lovers.save()

    mediterranean.toppings.add(Topping.objects.get(name="roasted eggplant"))
    mediterranean.toppings.add(Topping.objects.get(name="balsamic glaze"))

    hawaiian.toppings.add(Topping.objects.get(name="pineapple"))
    hawaiian.toppings.add(Topping.objects.get(name="smoked ham"))

    meat_lovers.toppings.add(Topping.objects.get(name="pepperoni"))
    meat_lovers.toppings.add(Topping.objects.get(name="capicola"))
    meat_lovers.toppings.add(Topping.objects.get(name="andouille sausage"))


class TestQuerysets(TestCase):
    def setUp(self) -> None:
        create_models()

    def test_queryset(self):
        queryset = Pizza.objects.all()
        feel = Feel(queryset)
        self.assertEqual(feel.count, 1)


class TestClassBasedViews(TestCase):
    def setUp(self) -> None:
        create_models()

    def test_list_view(self):
        feel = Feel(views.PizzaListView)
        self.assertEqual(feel.count, 7)

    def test_delete_view(self):
        self.assertRaises(TypeError, Feel(views.DeleteView))


class TestSerializers(TestCase):
    def setUp(self) -> None:
        create_models()

    def test_serializer_pizza(self):
        feel = Feel(PizzaSerializer)
        self.assertEqual(feel.count, 4)

    def test_serializer_topping(self):
        feel = Feel(ToppingSerializer)
        self.assertEqual(feel.count, 1)


class TestViews(TestCase):
    def setUp(self) -> None:
        create_models()

    def test_optimized_view(self):
        feel = Feel(views.pizza_list_optimized)
        self.assertEqual(feel.count, 2)

    def test_unoptimized_view(self):
        feel = Feel(views.pizza_list_unoptimized)
        self.assertEqual(feel.count, 7)


class TestFunctions(TestCase):
    def setUp(self) -> None:
        create_models()

    def test_function(self):
        def example_function():
            pizzas = Pizza.objects.all()
            for pizza in pizzas:
                list(pizza.toppings.all())

        feel = Feel(example_function)
        self.assertEqual(feel.count, 4)


class TestModelInstance(TestCase):
    def setUp(self) -> None:
        create_models()

    def test_model_instance(self):
        instance = Pizza.objects.get(name="Hawaiian")
        feel = Feel(instance)
        self.assertEqual(feel.count, 1)
