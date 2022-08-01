from typing import Type
from django.http import HttpRequest, HttpResponse
from django.db.models.query import QuerySet
from django.db import transaction
from django.db.models.query import ModelIterable
from inspect import signature, isclass

from .exceptions import error_messages

class Thing():
    '''Determine the real type of a thing

    A thing can be one of four types: 
    ['queryset', 'view', 'function', 'django_cbv', 'serializer']
    '''

    def __init__(self, thing, *args, **kwargs):
        self.thing = thing
        self.kwargs = kwargs
        self.thing_type = self.find_thing_type(thing)
        self.executor = self.find_executor_type(self.thing_type)

    def find_thing_type(self, thing) -> str:
        if type(thing) == QuerySet:
            thing_type = 'queryset'
        elif isclass(thing):
            if self.check_django_class_based_view(thing):
                thing_type = 'django_cbv'
            elif self.check_serializer(thing):
                thing_type = 'serializer'
            else:
                raise TypeError('Invalid Class')
        elif callable(thing): # all classes are callable but not all callables are classes
            if self.check_django_view(thing):
                thing_type = 'view'
            else:
                thing_type = 'function'
        else:
            if type(thing) == QuerySet:
                raise TypeError(error_messages['executed_query_error'])
            raise TypeError('Invalid Thing')
        return thing_type

    def check_django_view(self, thing):
        parameters = list(signature(thing).parameters)
        if 'request' not in parameters:
            return False
        response = thing(HttpRequest())
        if type(response) == HttpResponse:
            return True
        else:
            return False

    def check_django_class_based_view(self, thing):
        valid_cbvs = [
            "View",
            "TemplateView",
            "RedirectView",
            "ArchiveIndexView",
            "YearArchiveView",
            "MonthArchiveView",
            "WeekArchiveView",
            "DayArchiveView",
            "TodayArchiveView",
            "DateDetailView",
            "DetailView",
            "ListView",
            "GenericViewError",
        ]
        mro = thing.__mro__
        intersection = [x for x in mro if any(cbv in str(x) for cbv in valid_cbvs)]
        if intersection:
            return True
        else:
            return False

    def check_serializer(self, thing):
        mro = thing.__mro__
        valid_parent_class = 'rest_framework.serializers.ModelSerializer'
        if any(valid_parent_class in str(parent_class) for parent_class in mro):
            return True
        else:
            return False

    def find_executor_type(self, thing_type):
        if thing_type == 'queryset':
            return self.execute_queryset
        elif thing_type == 'view':
            return self.execute_view
        elif thing_type == 'function':
            return self.execute_function
        elif thing_type == 'django_cbv':
            return self.execute_django_cbv
        elif thing_type == 'serializer':
            return self.execute_serializer
        else:
            raise TypeError(f'Invalid Type: {thing_type}')

    def execute_queryset(self, thing):
        '''Run a Queryset
        
        when list() is called on a queryset the queryset's _result_cache
        is checked first. By calling list on the an instance of ModelIterable
        we can be sure that the queries are actually being run. 
        '''
        try:
            list(ModelIterable(thing))
        except Exception as e:
            raise e

    def execute_view(self, thing):
        request = self.kwargs.get('request', HttpRequest())
        try:
            thing(request)
        except Exception as e:
            raise e

    def execute_function(self, thing):
        try:
            thing()
        except Exception as e:
            raise e

    def execute_django_cbv(self, thing):
        if self.kwargs.get('request'):
            request = self.kwargs.get('request')
        else:
            request = HttpRequest()
            request.method = 'GET'
        try:
            response = thing.as_view()(request)
            response.render()
        except Exception as e:
            raise e

    def execute_serializer(self, thing):
        model = thing.Meta.model
        queryset = model.objects.all()
        if len(queryset) > 1:
            many = True
        else:
            many = False
        try:
            serializer_execution = thing(instance=queryset, many=many)
            serializer_execution.data
        except Exception as e:
            raise e

    def execute_thing(self):
        self.executor(self.thing)