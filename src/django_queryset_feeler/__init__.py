import sqlparse
import statistics
import warnings
from collections import Counter, OrderedDict
from sql_metadata import Parser as SQLParser
from pygments import highlight
from pygments.lexers import SqlLexer
from pygments.formatters import HtmlFormatter, TerminalTrueColorFormatter
from IPython.core.display import HTML, display
from time import perf_counter
from django.db import connection, reset_queries
from django.db.backends.base.base import BaseDatabaseWrapper

from .thing import Thing


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
    '''Format and add highlights to the SQL of a django queryset

    Can highlight jupyter notebooks using pygment's HTML highlighter

    As of now only highlights using one-dark styling
    '''
    query_string = query
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

class Feel():
    '''Get a feel for how the Django ORM is executing queries

    A lot goes into this
    '''

    def __init__(self, thing, iterations: int = 100, reset_queries_ok=True, *args, **kwargs):
        self.iterations = iterations
        self.reset_queries_ok = reset_queries_ok
        
        self.thing = Thing(thing, *args, **kwargs)
        self.type = self.thing.thing_type

        self.__times = None

    def flush_queries(self) -> None:
        if self.reset_queries_ok:
            reset_queries()
        else:
            max_queries = BaseDatabaseWrapper.queries_limit
            query_log_count = len(connection.queries)
            if len(query_log_count) >= max_queries:
                raise IndexError('Queries cannot be tracked once the max log count has been reached. Use django.db.reset_queries() to flush query log')
            
            query_threshhold = 500
            if len(query_log_count) > max_queries - query_threshhold:
                warnings.warn(f'Approaching query log limit. Currently {query_log_count} / {max_queries}')

    @property
    def query_time(self) -> float:
        '''Return the mean query time in microseconds. 
        The query will not be rerun every time this
        property is accessed. 
        '''
        if not self.__times:
            times = []
            for i in range(self.iterations):
                t0 = perf_counter()
                self.thing.execute_thing()
                t1 = perf_counter()
                duration = t1 - t0
                times.append(duration)
            self.times = times
        return statistics.mean(self.times)

    @property
    def query_count(self) -> int:
        self.flush_queries()
        self.thing.execute_thing()
        query_count = len(connection.queries)
        return query_count

    @property
    def report(self) -> None:
        table_dict = self.table_counts
        most_accessed_table = list(table_dict.items())[0][0]
        report = f'\
        \n           query count: {self.query_count} \
        \n      average duration: {round((self.query_time * 1000), 3)} ms \
        \n   most accessed table: {list(table_dict.items())[0][0]} - {list(table_dict.items())[0][1]} \
        \n         unique tables: {len(table_dict)} \
        \n              accessed \
        '
        return print(report)
        
    def __get_query_list(self) -> list:
        '''
        connection.queries returns a list of dictionaries containing the 
        sql query and the time it took to execute the query. This function 
        isolates just the sql query
        '''
        self.flush_queries()
        self.thing.execute_thing()

        queries = []
        for query in connection.queries:
            queries.append(query['sql'])

        return queries

    @property
    def sql_queries(self, pretty=True) -> None:
        for query in self.__get_query_list():
            if pretty:
                display_query(query)
            else:
                print(query)
    
    @property
    def table_counts(self) -> OrderedDict:
        self.flush_queries()
        self.thing.execute_thing()
        sql_list = [query['sql'] for query in connection.queries]
        tables = []
        for sql in sql_list:
            parsed = SQLParser(sql)
            queried_tables = parsed.tables
            tables += queried_tables
        table_counts = dict(Counter(tables))
        sorted_dict = dict(sorted(table_counts.items(), key=lambda x: x[1], reverse=True))
        return sorted_dict
