from email import message
from typing import Type


error_messages = {
    'executed_query_error': \
        '''
        A model instance was passed to a function where
        a queryset was expected. This is most likely
        caused by an accidental execution of the queryset.
        For more information see the Django models documentation:
        https://docs.djangoproject.com/en/4.0/ref/models/querysets/#methods-that-do-not-return-querysets
        ''',
}
