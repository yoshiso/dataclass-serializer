from dataclasses import dataclass
from typing import Any, Dict, Callable, Tuple, _GenericAlias  # type: ignore
import types

from collections import OrderedDict
from decimal import Decimal
from datetime import date, datetime
from importlib import import_module
import json
import dataclasses

__all__ = ["Serializable", "deserialize"]


META_FIELD = "__ser__"


class Serializable:
    def __post_init__(self):
        self._validate_contracts()

    def to_dict(self) -> dict:
        """Transform serializable object to dict.
        """
        fields = dataclasses.fields(self)
        o = {}
        for field in fields:
            o[field.name] = getattr(self, field.name)
        return o

    def serialize(self) -> dict:
        """Serialize object to be json serializable representation.
        """
        if not dataclasses.is_dataclass(self):
            raise TypeError("need to be decorated as dataclass")

        fields = dataclasses.fields(self)

        o = {}

        for field in fields:

            value = getattr(self, field.name)

            if value is None:
                # Allow to be optional only when Optional type is declared.
                if not isinstance(field.type, _GenericAlias):
                    raise TypeError(f"{field.name} is not optional")

                if not type(None) in getattr(field.type, "__args__"):
                    raise TypeError(f"{field.name} is not optional")

            if field.metadata is not None:

                encode = field.metadata.get("encode", None)

                if encode is not None:
                    if field.metadata.get("decode") is None:
                        raise ValueError(
                            "decode is not implemented for {} in {}".format(
                                field.name, self.__class__.__name__
                            )
                        )
                    value = encode(value)

            value = _serialize(value)

            o[field.name] = value

        o["__ser__"] = "{}:{}".format(
            self.__class__.__module__, self.__class__.__name__
        )

        return o

    def _validate_contracts(self):
        """Check varidity of contraacts.
        """
        fields = dataclasses.fields(self)

        for field in fields:

            value = getattr(self, field.name)

            if value is None:
                # Allow to be optional only when Optional type is declared.
                if not isinstance(field.type, _GenericAlias):
                    raise TypeError(f"{field.name} is not optional")

                if not type(None) in getattr(field.type, "__args__"):
                    raise TypeError(f"{field.name} is not optional")

            contract = field.metadata.get("contract", None)

            if contract is not None:
                if value is not None and not contract(value):
                    raise ValueError(
                        f"break the contract for {field.name}, {self.__class__.__name__}"
                    )

    def validate(self):
        """validate if object can serialize / deserialize correctly.
        """
        self._validate_contracts()
        if self != self.__class__.deserialize(json.loads(json.dumps(self.serialize()))):
            raise ValueError("could not be deserialized with same value")

    @classmethod
    def deserialize(cls, data: dict) -> "Serializable":
        data = data.copy()

        data.pop(META_FIELD, None)

        o: Dict[str, Any] = {}

        for field in dataclasses.fields(cls):

            value = data.get(field.name, _default_value(field))

            if value == dataclasses.MISSING:
                raise ValueError(
                    "deserialized with unknown value for {} in {}".format(
                        field.name, cls.__name__
                    )
                )

            value = _deserialize(value)

            if field.metadata is not None:

                decode = field.metadata.get("decode", None)
                if decode is not None:
                    value = decode(value)

            o[field.name] = value

        return cls(**o)  # type: ignore


@dataclass(frozen=True)
class Partial(Serializable):
    func: Callable
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


def partial(func: Callable, *args, **kwargs) -> Partial:
    """Create partial function / class"""
    return Partial(func=func, args=args, kwargs=kwargs)


def _serialize(x):
    if isinstance(x, OrderedDict):
        return {META_FIELD: "OrderedDict", "value": [list(xi) for xi in x.items()]}
    if isinstance(x, dict):
        return {k: _serialize(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_serialize(xi) for xi in x]
    if isinstance(x, tuple):
        return {META_FIELD: "tuple", "value": [_serialize(xi) for xi in x]}
    if isinstance(x, set):
        return {META_FIELD: "set", "value": list(x)}
    if isinstance(x, Serializable):
        return x.serialize()
    if isinstance(x, type):
        return {META_FIELD: "type", "value": f"{x.__module__}:{x.__name__}"}
    if isinstance(x, types.FunctionType):
        return {META_FIELD: "function", "value": f"{x.__module__}:{x.__name__}"}
    if isinstance(x, datetime):
        return {META_FIELD: "datetime", "value": x.isoformat()}
    if isinstance(x, date):
        return {META_FIELD: "date", "value": x.strftime("%Y%m%d")}
    if isinstance(x, Decimal):
        return {META_FIELD: "Decimal", "value": str(x)}
    return x


def _deserialize(x):
    if isinstance(x, dict):
        if META_FIELD in x:
            if x[META_FIELD] == "OrderedDict":
                return OrderedDict([(v[0], _deserialize(v[1])) for v in x["value"]])
            elif x[META_FIELD] == "tuple":
                return tuple([_deserialize(xi) for xi in x["value"]])
            elif x[META_FIELD] == "set":
                return set([_deserialize(xi) for xi in x["value"]])
            elif x[META_FIELD] == "datetime":
                return datetime.fromisoformat(x["value"])
            elif x[META_FIELD] == "date":
                return datetime.strptime(x["value"], "%Y%m%d").date()
            elif x[META_FIELD] == "Decimal":
                return Decimal(x["value"])
            elif x[META_FIELD] in ("type", "function"):
                m, c = x["value"].split(":")
                return getattr(import_module(m), c)
            m, c = x[META_FIELD].split(":")
            cls = getattr(import_module(m), c)
            return cls.deserialize(x)
        return {k: _deserialize(v) for k, v in x.items()}
    elif isinstance(x, list):
        return [_deserialize(xi) for xi in x]
    else:
        return x


deserialize = _deserialize


def _default_value(x: dataclasses.Field):
    if x.default != dataclasses.MISSING:
        return x.default
    elif x.default_factory != dataclasses.MISSING:  # type: ignore
        return x.default_factory()  # type: ignore
    else:
        return x.default
