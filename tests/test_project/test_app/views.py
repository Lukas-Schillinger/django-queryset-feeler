from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, DeleteView

from .models import Pizza, Topping



def pizza_list_unoptimized(request):
    pizzas = Pizza.objects.all()
    return render(request, 'test_app/pizza_list.html', {'pizzas': pizzas})

def pizza_list_optimized(request):
    pizzas = Pizza.objects.all().prefetch_related('toppings')
    return render(request, 'test_app/pizza_list.html', {'pizzas': pizzas})

class PizzaListView(ListView):
    model = Pizza
    context_object_name = 'pizzas'
    template_name = 'test_app/pizza_list.html'

class PizzaDeleteView(DeleteView):
    model = Pizza
    success_url = reverse_lazy('pizza_list_listview')