from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
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


async def pizza_list_async(request):
    """Async FBV — mirrors the sync unoptimized view (N+1 pattern)."""
    data = []
    async for pizza in Pizza.objects.all():  # 1 query
        toppings = [t.name async for t in pizza.toppings.all()]  # N queries
        data.append({"name": pizza.name, "toppings": toppings})
    return JsonResponse({"pizzas": data}, safe=False)


class AsyncPizzaListView(View):
    """Async CBV using async ORM methods."""

    async def get(self, request):
        count = await Pizza.objects.acount()  # 1 query
        first = await Pizza.objects.afirst()  # 1 query
        return JsonResponse({"count": count, "first": first.name})
