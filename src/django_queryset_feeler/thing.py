"""Detect and execute different Django object types for profiling."""

from __future__ import annotations

from asyncio import iscoroutinefunction
from inspect import isclass, signature
from typing import TYPE_CHECKING, Any

from asgiref.sync import async_to_sync
from django.db.models import Model
from django.db.models.query import ModelIterable, QuerySet
from django.http import HttpRequest
from django.views import View

if TYPE_CHECKING:
    from collections.abc import Callable


def _is_drf_serializer(cls: type) -> bool:
    """Check if cls is a DRF serializer using issubclass, not string matching."""
    try:
        from rest_framework.serializers import BaseSerializer
    except ImportError:
        return False
    return issubclass(cls, BaseSerializer)


def _has_request_param(func: Callable[..., Any]) -> bool:
    """Check if a callable accepts a 'request' parameter (likely a Django view)."""
    try:
        return "request" in signature(func).parameters
    except (ValueError, TypeError):
        return False


# Each entry: (detector, type_name)
# Order matters — most specific first, callable/function last (catchall)
HANDLERS: list[tuple[Callable[[Any], bool], str]] = [
    (lambda t: isinstance(t, QuerySet), "queryset"),
    (lambda t: isclass(t) and issubclass(t, View), "cbv"),
    (lambda t: isclass(t) and _is_drf_serializer(t), "serializer"),
    (lambda t: isinstance(t, Model), "model_instance"),
    (lambda t: callable(t) and _has_request_param(t), "view"),
    (lambda t: callable(t), "function"),
]


class Thing:
    """Wraps a Django object and provides a uniform execute() interface.

    Supported types: QuerySet, class-based view, DRF serializer,
    model instance, function-based view, plain function.
    """

    def __init__(self, thing: Any, request: HttpRequest | None = None) -> None:
        self.thing = thing
        self._request = request
        self.thing_type = self._detect_type(thing)

    def _detect_type(self, thing: Any) -> str:
        """Determine the type of thing using the handler table."""
        for detector, type_name in HANDLERS:
            if detector(thing):
                return type_name
        msg = (
            "Invalid Thing. Valid things are querysets, class-based views, "
            "serializers, views, functions, and model instances."
        )
        raise TypeError(msg)

    def _get_request(self) -> HttpRequest:
        """Return the provided request or create an empty one."""
        if self._request is not None:
            return self._request
        return HttpRequest()

    def execute(self) -> None:
        """Execute the thing, dispatching to the appropriate handler."""
        executors: dict[str, Callable[[], None]] = {
            "queryset": self._execute_queryset,
            "cbv": self._execute_cbv,
            "serializer": self._execute_serializer,
            "model_instance": self._execute_model_instance,
            "view": self._execute_view,
            "function": self._execute_function,
        }
        executors[self.thing_type]()

    def _execute_queryset(self) -> None:
        """Execute a QuerySet bypassing the result cache."""
        list(ModelIterable(self.thing))

    def _execute_view(self) -> None:
        """Execute a function-based view with an HttpRequest."""
        func = self.thing
        if iscoroutinefunction(func):
            func = async_to_sync(func)
        func(self._get_request())

    def _execute_function(self) -> None:
        """Execute a plain function with no arguments."""
        func = self.thing
        if iscoroutinefunction(func):
            func = async_to_sync(func)
        func()

    def _execute_cbv(self) -> None:
        """Execute a class-based view via as_view()."""
        request = self._get_request()
        request.method = "GET"
        view_func = self.thing.as_view()
        if iscoroutinefunction(view_func):
            view_func = async_to_sync(view_func)
        response = view_func(request)
        if hasattr(response, "render"):
            response.render()

    def _execute_serializer(self) -> None:
        """Execute a DRF serializer against all instances of its Meta.model."""
        model = self.thing.Meta.model
        queryset = model.objects.all()
        many = len(queryset) > 1
        serializer = self.thing(instance=queryset, many=many)
        serializer.data  # noqa: B018 — accessing .data triggers serialization

    def _execute_model_instance(self) -> None:
        """Re-fetch a model instance from the database."""
        self.thing.refresh_from_db()
