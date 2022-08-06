from django import template

register = template.Library()

@register.filter(name='is_vegetarian')
def is_vegetarian(value):
    if any(topping.vegetarian == False for topping in value):
        return False
    else:
        return True