from django.conf import settings
from django.test import TestCase

from django_queryset_feeler import Feel, Query

from . import views
from .models import Pizza, Topping
from .serializers import PizzaSerializer, ToppingSerializer

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
    def setUp(self):
        create_models()

    def test_queryset(self):
        queryset = Pizza.objects.all()
        feel = Feel(queryset)
        self.assertEqual(feel.count, 1)


class TestClassBasedViews(TestCase):
    def setUp(self):
        create_models()

    def test_list_view(self):
        feel = Feel(views.PizzaListView)
        self.assertEqual(feel.count, 7)


class TestSerializers(TestCase):
    def setUp(self):
        create_models()

    def test_serializer_pizza(self):
        feel = Feel(PizzaSerializer)
        self.assertEqual(feel.count, 4)

    def test_serializer_topping(self):
        feel = Feel(ToppingSerializer)
        self.assertEqual(feel.count, 1)


class TestViews(TestCase):
    def setUp(self):
        create_models()

    def test_optimized_view(self):
        feel = Feel(views.pizza_list_optimized)
        self.assertEqual(feel.count, 2)

    def test_unoptimized_view(self):
        feel = Feel(views.pizza_list_unoptimized)
        self.assertEqual(feel.count, 7)


class TestFunctions(TestCase):
    def setUp(self):
        create_models()

    def test_function(self):
        def example_function():
            pizzas = Pizza.objects.all()
            for pizza in pizzas:
                list(pizza.toppings.all())

        feel = Feel(example_function)
        self.assertEqual(feel.count, 4)


class TestModelInstance(TestCase):
    def setUp(self):
        create_models()

    def test_model_instance(self):
        instance = Pizza.objects.get(name="Hawaiian")
        feel = Feel(instance)
        self.assertEqual(feel.count, 1)


class TestProperties(TestCase):
    def setUp(self):
        create_models()
        self.feel = Feel(Pizza.objects.all())

    def test_sql(self):
        result = self.feel.sql
        self.assertIsInstance(result, str)
        self.assertIn("tests_pizza", result)

    def test_tables(self):
        result = self.feel.tables
        self.assertIsInstance(result, dict)
        self.assertIn("tests_pizza", result)
        self.assertEqual(result["tests_pizza"], 1)

    def test_time(self):
        result = self.feel.time
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_report(self):
        result = self.feel.report
        self.assertIsInstance(result, str)
        self.assertIn("query count: 1", result)

    def test_queries(self):
        result = self.feel.queries
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), self.feel.count)
        for q in result:
            self.assertIsInstance(q, Query)
            self.assertIsInstance(q.sql, str)
            self.assertIsInstance(q.time, str)
            self.assertIsInstance(q.table, str)


class TestToDict(TestCase):
    def setUp(self):
        create_models()

    def test_to_dict(self):
        feel = Feel(Pizza.objects.all())
        result = feel.to_dict()
        self.assertIsInstance(result, dict)
        self.assertEqual(result["type"], "queryset")
        self.assertEqual(result["count"], 1)
        self.assertIn("time_ms", result)
        self.assertIn("tables", result)
        self.assertIsInstance(result["queries"], list)
        self.assertEqual(len(result["queries"]), 1)


class TestRepr(TestCase):
    def setUp(self):
        create_models()

    def test_repr(self):
        feel = Feel(Pizza.objects.all())
        result = repr(feel)
        self.assertTrue(result.startswith("Feel("))
        self.assertIn("count=1", result)


class TestProfile(TestCase):
    def setUp(self):
        create_models()

    def test_profile(self):
        with Feel.profile() as f:
            list(Pizza.objects.all())
        self.assertEqual(f.count, 1)
        self.assertIn("tests_pizza", f.tables)


class TestInvalidThing(TestCase):
    def test_invalid_thing(self):
        with self.assertRaises(TypeError):
            Feel("not a valid thing")

    def test_invalid_thing_int(self):
        with self.assertRaises(TypeError):
            Feel(42)


class TestCaching(TestCase):
    def setUp(self):
        create_models()

    def test_count_is_stable(self):
        feel = Feel(Pizza.objects.all())
        first = feel.count
        second = feel.count
        self.assertEqual(first, second)
