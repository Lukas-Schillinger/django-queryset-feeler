from django import template

register = template.Library()


@register.filter(name="is_vegetarian")
def is_vegetarian(value):
    return all(topping.vegetarian for topping in value)
