from __future__ import annotations

import json
from enum import Enum
from typing import Any, get_args, get_origin


try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:  # pragma: no cover
    ConfigDict = dict

    class _FieldInfo:
        def __init__(self, default: Any = None, default_factory: Any | None = None) -> None:
            self.default = default
            self.default_factory = default_factory

    def Field(default: Any = None, default_factory: Any | None = None, **_: Any) -> Any:
        return _FieldInfo(default=default, default_factory=default_factory)

    class BaseModel:
        model_config = ConfigDict()

        def __init__(self, **data: Any) -> None:
            annotations = self._collect_annotations()
            for name, annotation in annotations.items():
                if name in data:
                    value = data[name]
                elif hasattr(self.__class__, name):
                    field_value = getattr(self.__class__, name)
                    if isinstance(field_value, _FieldInfo):
                        if field_value.default_factory is not None:
                            value = field_value.default_factory()
                        else:
                            value = field_value.default
                    else:
                        value = field_value
                else:
                    value = None
                setattr(self, name, self._coerce_value(annotation, value))

        @classmethod
        def _collect_annotations(cls) -> dict[str, Any]:
            annotations: dict[str, Any] = {}
            for base in reversed(cls.__mro__):
                annotations.update(getattr(base, "__annotations__", {}))
            return annotations

        @classmethod
        def _coerce_value(cls, annotation: Any, value: Any) -> Any:
            if value is None:
                return None

            origin = get_origin(annotation)
            args = get_args(annotation)

            if origin is list and args:
                return [cls._coerce_value(args[0], item) for item in value]
            if origin is dict and len(args) == 2:
                return {
                    key: cls._coerce_value(args[1], item)
                    for key, item in value.items()
                }
            if origin is not None and type(None) in args:
                non_none = [arg for arg in args if arg is not type(None)]
                if len(non_none) == 1:
                    return cls._coerce_value(non_none[0], value)
            if isinstance(annotation, type):
                if issubclass(annotation, Enum):
                    return value if isinstance(value, annotation) else annotation(value)
                if issubclass(annotation, BaseModel):
                    return value if isinstance(value, annotation) else annotation(**value)
            return value

        @classmethod
        def model_validate(cls, data: Any) -> "BaseModel":
            if isinstance(data, cls):
                return data
            return cls(**data)

        def model_dump(self) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for name in self._collect_annotations():
                result[name] = self._dump_value(getattr(self, name, None))
            return result

        @classmethod
        def _dump_value(cls, value: Any) -> Any:
            if isinstance(value, BaseModel):
                return value.model_dump()
            if isinstance(value, Enum):
                return value.value
            if isinstance(value, list):
                return [cls._dump_value(item) for item in value]
            if isinstance(value, dict):
                return {key: cls._dump_value(item) for key, item in value.items()}
            return value

        def model_dump_json(self, indent: int | None = None) -> str:
            return json.dumps(self.model_dump(), indent=indent)
