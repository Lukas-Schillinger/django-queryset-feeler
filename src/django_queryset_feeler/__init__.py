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
        shell = get_ipython().__class__.__name__  # type: ignore
        if shell == "ZMQInteractiveShell":
            return True  # Jupyter notebook or qtconsole
        elif shell == "TerminalInteractiveShell":
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False  # Probably standard Python interpreter


def highlight_query(query):
    """Format and add highlights to the SQL of a django queryset

    Can highlight jupyter notebooks using pygment's HTML highlighter

    As of now only highlights using one-dark styling
    """
    query_string = query
    formatted_string = sqlparse.format(query_string, reindent=True)

    if is_notebook():
        formatter = HtmlFormatter(
            full=True,
            nobackground=True,
            style="one-dark",
        )
    else:
        formatter = TerminalTrueColorFormatter(
            style="one-dark",
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


class Feel:
    """Get a feel for how the Django ORM is executing queries

    `thing` is the thing being profiled. This can be a `view`, a `class_based_view`,
    a `queryset`, a `model_instance`, a `serializer`, or a regular function.

    `iterations` is the number of times the Thing is executed to measure `query_time`.
    Default is 32

    `reset_queries_ok` checks if it's okay to delete the query history in
    `django.db.connections.queries`. Default is True
    """

    def __init__(
        self,
        thing,
        iterations: int = 32,
        reset_queries_ok=True,
        execution_args=None,
        request=None,
        instance=None,
        *args,
        **kwargs,
    ):
        self.iterations = iterations
        self.reset_queries_ok = reset_queries_ok

        self.execution_dict = {
            "execution_args": execution_args,
            "request": request,
            "instance": instance,
        }

        self.thing = Thing(thing, self.execution_dict, *args, **kwargs)
        self.type = self.thing.thing_type

        self.__times = None

    def flush_queries(self) -> None:
        if self.reset_queries_ok:
            reset_queries()
        else:
            max_queries = BaseDatabaseWrapper.queries_limit
            query_log_count = len(connection.queries)
            if query_log_count >= max_queries:
                raise IndexError(
                    "Queries cannot be tracked once the max log count has been reached. Use django.db.reset_queries() to flush query log"
                )

            query_threshhold = 500
            if query_log_count > max_queries - query_threshhold:
                warnings.warn(
                    f"Approaching query log limit. Currently {query_log_count} / {max_queries}"
                )

    @property
    def time(self) -> float:
        """Return the mean query time in microseconds.

        The query will not be rerun every time the property is accessed.
        """
        if not self.__times:
            times = []
            for i in range(self.iterations):
                t0 = perf_counter()
                self.thing.execute_thing()
                t1 = perf_counter()
                duration = t1 - t0
                times.append(duration)
            self.__times = times
        return statistics.mean(self.__times)

    @property
    def count(self) -> int:
        self.flush_queries()
        self.thing.execute_thing()
        query_count = len(connection.queries)
        return query_count

    @property
    def report(self) -> None:
        table_dict = self.tables
        report = f"\
        \n           query count: {self.count} \
        \n      average duration: {round((self.time * 1000), 3)} ms \
        \n   most accessed table: {list(table_dict.items())[0][0]} - {list(table_dict.items())[0][1]} \
        \n         unique tables: {len(table_dict)} \
        \n              accessed \
        "
        return print(report)

    def __get_query_list(self) -> list:
        """
        connection.queries returns a list of dictionaries containing the
        sql query and the time it took to execute the query. This function
        isolates just the sql query
        """
        self.flush_queries()
        self.thing.execute_thing()

        queries = []
        for query in connection.queries:
            queries.append(query["sql"])

        return queries

    @property
    def sql(self, pretty=True) -> None:
        for query in self.__get_query_list():
            if pretty:
                display_query(query)
            else:
                print(query)

    @property
    def tables(self) -> OrderedDict:
        self.flush_queries()
        self.thing.execute_thing()
        sql_list = [query["sql"] for query in connection.queries]
        tables = []
        for sql in sql_list:
            parsed = SQLParser(sql)
            queried_tables = parsed.tables
            tables += queried_tables
        table_counts = dict(Counter(tables))
        sorted_dict = OrderedDict(
            sorted(table_counts.items(), key=lambda x: x[1], reverse=True)
        )
        return sorted_dict
