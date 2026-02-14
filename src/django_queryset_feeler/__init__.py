"""django-queryset-feeler: profile Django ORM queries with ease."""

from __future__ import annotations

__all__ = ["Feel", "FormattedString", "Query"]

import statistics
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter
from typing import TYPE_CHECKING, Any

import sqlparse
from django.db import connection, reset_queries
from pygments import highlight
from pygments.formatters import HtmlFormatter, TerminalTrueColorFormatter
from pygments.lexers import SqlLexer
from sql_metadata import Parser as SQLParser

from .thing import Thing

if TYPE_CHECKING:
    from collections.abc import Generator

    from django.http import HttpRequest


def _is_notebook() -> bool:
    """Detect if code is running in a Jupyter notebook."""
    try:
        shell = get_ipython().__class__.__name__  # type: ignore[name-defined]
    except NameError:
        return False
    return shell == "ZMQInteractiveShell"


def _format_sql(sql: str) -> str:
    """Format and syntax-highlight a SQL string."""
    formatted = sqlparse.format(sql, reindent=True)

    if _is_notebook():
        formatter = HtmlFormatter(full=True, nobackground=True, style="one-dark")
    else:
        formatter = TerminalTrueColorFormatter(style="one-dark")

    return highlight(code=formatted, lexer=SqlLexer(), formatter=formatter)


def _extract_table(sql: str) -> str:
    """Extract the primary table name from a SQL query."""
    try:
        tables = SQLParser(sql).tables
    except ValueError:
        return "<unknown>"
    return tables[0] if tables else "<unknown>"


class FormattedString(str):
    """String that displays its contents (not repr) in the REPL."""

    def __repr__(self) -> str:
        """Return the string itself so REPL output is formatted."""
        return str(self)


@dataclass(frozen=True)
class Query:
    """A single captured database query."""

    sql: str
    time: str
    table: str


class Feel:
    """Profile Django ORM query execution.

    Pass any Django object (queryset, view, CBV, serializer, model instance,
    or function) and inspect the queries it generates.

    Args:
        thing: The object to profile.
        iterations: Number of runs for timing (default 32).
        request: Optional HttpRequest to use for views/CBVs.

    """

    def __init__(
        self,
        thing: Any,
        *,
        iterations: int = 32,
        request: HttpRequest | None = None,
    ) -> None:
        self._thing = Thing(thing, request=request)
        self._iterations = iterations
        self._queries: list[Query] | None = None
        self._times: list[float] | None = None

    def _execute(self) -> None:
        """Execute the thing once and snapshot the queries."""
        if self._queries is not None:
            return
        reset_queries()
        self._thing.execute()
        self._queries = [
            Query(sql=q["sql"], time=q["time"], table=_extract_table(q["sql"]))
            for q in connection.queries
        ]

    @property
    def queries(self) -> list[Query]:
        """Individual queries from the execution."""
        self._execute()
        assert self._queries is not None
        return list(self._queries)

    @property
    def count(self) -> int:
        """Number of database queries executed."""
        self._execute()
        assert self._queries is not None
        return len(self._queries)

    @property
    def sql(self) -> str:
        """Formatted SQL of all queries, separated by blank lines."""
        self._execute()
        assert self._queries is not None
        return FormattedString("\n\n".join(_format_sql(q.sql) for q in self._queries))

    @property
    def tables(self) -> dict[str, int]:
        """Table access counts, sorted by frequency (descending)."""
        self._execute()
        assert self._queries is not None
        counts = Counter(q.table for q in self._queries)
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    @property
    def time(self) -> float:
        """Mean execution time in seconds across iterations."""
        if self._times is None:
            self._times = [self._benchmark_once() for _ in range(self._iterations)]
        return statistics.mean(self._times)

    def _benchmark_once(self) -> float:
        """Run the thing once and return the wall-clock duration."""
        t0 = perf_counter()
        self._thing.execute()
        return perf_counter() - t0

    @property
    def report(self) -> str:
        """Human-readable summary of query profiling results."""
        lines = [
            f"  query count: {self.count}",
            f"     duration: {round(self.time * 1000, 3)} ms",
            f"unique tables: {len(self.tables)}",
        ]
        if self.tables:
            top_table, top_count = next(iter(self.tables.items()))
            lines.append(f" most accessed: {top_table} ({top_count})")
        return FormattedString("\n".join(lines))

    def to_dict(self) -> dict[str, Any]:
        """Structured output for programmatic consumption."""
        return {
            "type": self._thing.thing_type,
            "count": self.count,
            "time_ms": round(self.time * 1000, 3),
            "tables": self.tables,
            "queries": [
                {"sql": q.sql, "time": q.time, "table": q.table} for q in self.queries
            ],
        }

    def __repr__(self) -> str:
        """Show key stats at a glance in REPL/notebook."""
        return (
            f"Feel(type={self._thing.thing_type}, count={self.count}, "
            f"time={round(self.time * 1000, 3)}ms, tables={len(self.tables)})"
        )

    @classmethod
    @contextmanager
    def profile(cls) -> Generator[Feel, None, None]:
        """Context manager for profiling arbitrary code blocks.

        Usage::

            with Feel.profile() as f:
                pizzas = Pizza.objects.all()
                for p in pizzas:
                    list(p.toppings.all())
            print(f.count)
        """
        reset_queries()
        result = cls.__new__(cls)
        result._queries = None
        result._times = None
        result._iterations = 32
        yield result
        # Snapshot queries after the block executes
        result._queries = [
            Query(sql=q["sql"], time=q["time"], table=_extract_table(q["sql"]))
            for q in connection.queries
        ]
