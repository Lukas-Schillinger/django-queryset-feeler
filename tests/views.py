from django.shortcuts import render
from django.views.generic import ListView

from .models import Pizza


def pizza_list_unoptimized(request):
    pizzas = Pizza.objects.all()
    return render(request, "tests/pizza_list.html", {"pizzas": pizzas})


def pizza_list_optimized(request):
    pizzas = Pizza.objects.all().prefetch_related("toppings")
    return render(request, "tests/pizza_list.html", {"pizzas": pizzas})


class PizzaListView(ListView):
    model = Pizza
    context_object_name = "pizzas"
    template_name = "tests/pizza_list.html"
