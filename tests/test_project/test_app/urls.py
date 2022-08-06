from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('pizza_list_unoptimized', views.pizza_list_unoptimized, name='pizza_list_unoptimized'),
    path('pizza_list_optimized', views.pizza_list_optimized, name='pizza_list_optimized'),
    path('pizza_list_listview', views.PizzaListView.as_view(), name='pizza_list_listview'),
    path('pizza_list_deleteview/<int:pk>', views.PizzaDeleteView.as_view(), name='pizza_list_deleteview'),
]