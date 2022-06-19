import sqlparse
import statistics
from pygments import highlight
from pygments.lexers import SqlLexer
from pygments.formatters import HtmlFormatter, TerminalTrueColorFormatter
from IPython.core.display import HTML, display
from datetime import datetime
from inspect import cleandoc

from django.db import connection, reset_queries
from django.db.models.query import QuerySet
from django.db.models.base import ModelBase

def is_notebook():
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter

def highlight_query(query):
    if isinstance(query, QuerySet):
        query_string = str(query.query)
    elif isinstance(query, str):
        query_string = query
    elif isinstance((query.__class__).__base__, ModelBase):
        error_message = cleandoc(f'''
        A model was passed to highlight_query(). This most likely happened because 
        the intended queryset was accidentally evaluated. See 
        https://docs.djangoproject.com/en/4.0/ref/models/querysets/#methods-that-do-not-return-querysets
        for more information. 
        ''')
        raise TypeError(error_message)
    else:
        error_message = cleandoc(f'''
        An invalid object type ({type(query)}) was passed to highlight_query(). Only 
        querysets or string representations of SQL queries can be used. 
        ''')
        raise TypeError(error_message)

    formatted_string = sqlparse.format(query_string, reindent=True)

    if is_notebook():
        formatter = HtmlFormatter(
            full=True,
            nobackground=True,
            style='one-dark',
        )
    else:
        formatter = TerminalTrueColorFormatter(
            style='one-dark',
        )

    hightlighted_query = highlight(
        code=formatted_string,
        lexer=SqlLexer(),
        formatter=formatter,
    )
    return hightlighted_query

def display_query(query):
    highlighted_query = highlight_query(query)
    if is_notebook():
        display(HTML(highlighted_query))
    else:
        print(highlighted_query)


class QueryInspection():
    def __init__(self, function, iterations=100):
        self.function = function
        self.iterations = iterations
        self.times = None
        self.query_time = self.get_query_time()

    def get_query_time(self):
        '''
        Return the mean query time in microseconds. Will not re-run the query timer
        if it has already been created. 
        '''
        if not self.times:
            times = []
            for i in range(self.iterations):
                t0 = datetime.now()
                self.function()
                duration = datetime.now() - t0
                times.append(duration.microseconds)
            self.times = times
        return statistics.mean(self.times)

    def count_queries(self) -> int:
        reset_queries()
        self.function()
        query_count = len(connection.queries)
        return query_count
        
    def get_query_list(self) -> list:
        '''
        connection.queries returns a list of dictionaries containing the 
        sql query and the time it took to execute the query. This function 
        isolates just the sql query
        '''
        reset_queries()
        self.function()

        queries = []
        for query in connection.queries:
            queries.append(query['sql'])

        return queries

    def iterate_queries(self, pretty=True) -> None:
        for query in self.get_query_list():
            if pretty:
                display_query(query)
            else:
                print(query)
    