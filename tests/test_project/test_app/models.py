from django.utils.functional import cached_property
from django.db import models


class Topping(models.Model):
    name = models.CharField(max_length=100)
    vegetarian = models.BooleanField()

    def __str__(self):
        return self.name


class Pizza(models.Model):
    name = models.CharField(max_length=100)
    toppings = models.ManyToManyField(Topping)

    def __str__(self):
        return self.name