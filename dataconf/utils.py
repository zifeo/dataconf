import dataclasses
import re
from collections.abc import Sequence
from dataclasses import MISSING
from dataclasses import asdict
from dataclasses import fields
from dataclasses import is_dataclass
from datetime import date
from datetime import datetime
from datetime import timedelta
from enum import Enum
from enum import IntEnum
from inspect import isclass
from pathlib import Path
from types import UnionType
from typing import Any
from typing import ForwardRef
from typing import Literal
from typing import Union
from typing import get_args
from typing import get_origin
from typing import get_type_hints
from uuid import UUID

import pyparsing
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
from isodate import Duration
from isodate import duration_isoformat
from isodate import parse_duration
from pyhocon import ConfigFactory
from pyhocon.config_tree import ConfigList
from pyhocon.config_tree import ConfigTree

from dataconf.exceptions import AmbiguousSubclassException
from dataconf.exceptions import EnvListFormatException
from dataconf.exceptions import EnvListOrderException
from dataconf.exceptions import MalformedConfigException
from dataconf.exceptions import MissingTypeException
from dataconf.exceptions import ParseException
from dataconf.exceptions import TypeConfigException
from dataconf.exceptions import UnexpectedKeysException

NoneType = type(None)

_BOOL_TRUE = {"true", "1", "yes", "on", "t", "y"}
_BOOL_FALSE = {"false", "0", "no", "off", "f", "n"}


def __parse_bool(value: Any):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalised = value.strip().lower()
        if normalised in _BOOL_TRUE:
            return True
        if normalised in _BOOL_FALSE:
            return False
    return None


def __parse_type(value: Any, clazz: type, path: str, check: bool):
    try:
        if check:
            return value
    except TypeError:
        pass

    raise TypeConfigException(
        f"expected type {clazz} at {path_to_str(path)}, got {type(value)}"
    )


def is_union(origin):
    return origin is Union or origin is UnionType


def is_optional(type: type | Any | str):
    # Optional = Union[T, NoneType]
    return is_union(get_origin(type)) and NoneType in get_args(type)


_UNION_CATCH = (
    TypeConfigException,
    MalformedConfigException,
    UnexpectedKeysException,
    ParseException,
    TypeError,
    ValueError,
    KeyError,
    AttributeError,
)

_ENV_KEY_PARTS = re.compile(r"(\d+)")


def _type_hints(clazz: type) -> dict[str, Any]:
    try:
        return get_type_hints(clazz)
    except (NameError, TypeError, AttributeError):
        return {}


def _is_mapping(value: Any) -> bool:
    return isinstance(value, (ConfigTree, dict)) and not isinstance(value, ConfigList)


def _plain(value: Any) -> Any:
    if isinstance(value, ConfigTree):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, ConfigList)):
        return [_plain(v) for v in value]
    return value


def _sequence_from(value: Any, path: str, clazz: type):
    if value is None:
        raise MalformedConfigException(
            f"expected list at {path_to_str(path)} but received None"
        )
    if isinstance(value, str):
        raise TypeConfigException(
            f"expected type {clazz} at {path_to_str(path)}, got {type(value)}"
        )
    if isinstance(value, ConfigTree):
        keys = list(value.keys())
        try:
            idxs = [int(k) for k in keys]
        except (TypeError, ValueError):
            raise TypeConfigException(
                f"expected type {clazz} at {path_to_str(path)}, got {type(value)}"
            )
        if set(idxs) != set(range(len(idxs))):
            raise TypeConfigException(
                f"expected type {clazz} at {path_to_str(path)}, got {type(value)}"
            )
        return [value[k] for k in sorted(keys, key=lambda k: int(k))]
    if isinstance(value, (list, tuple, ConfigList)):
        return list(value)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return list(value)
    raise TypeConfigException(
        f"expected type {clazz} at {path_to_str(path)}, got {type(value)}"
    )


def _relativedelta_iso(value: relativedelta) -> str:
    return duration_isoformat(
        Duration(
            years=value.years,
            months=value.months,
            days=value.days,
            hours=value.hours,
            minutes=value.minutes,
            seconds=value.seconds + value.microseconds / 1_000_000,
        )
    )


def _has_index(focus, key) -> bool:
    if isinstance(focus, list):
        return isinstance(key, int) and 0 <= key < len(focus)
    return key in focus


def __parse(value: any, clazz: type, path: str, strict: bool, ignore_unexpected: bool):
    if isinstance(clazz, (str, ForwardRef)):
        raise TypeConfigException(
            f"unresolved type annotation {clazz!r} at {path_to_str(path)}"
        )

    supertype = getattr(clazz, "__supertype__", None)
    if supertype is not None:
        return __parse(value, supertype, path, strict, ignore_unexpected)

    if is_dataclass(clazz):
        if not _is_mapping(value):
            raise TypeConfigException(
                f"expected type {clazz} at {path_to_str(path)}, got {type(value)}"
            )

        fs = {}
        used_keys = set()
        hints = _type_hints(clazz)

        for f in fields(clazz):
            if not f.init:
                continue
            ftype = hints.get(f.name, f.type)
            if isinstance(ftype, (str, ForwardRef)):
                raise TypeConfigException(
                    f"unresolved type annotation {ftype!r} at {path_to_str(path)}.{f.name}"
                )
            if f.name in value:
                val = value[f.name]
                used_keys.add(f.name)
            elif f.name.replace("_", "-") in value:
                used_keys.add(f.name.replace("_", "-"))
                val = value[f.name.replace("_", "-")]
            else:
                if callable(f.default_factory):
                    val = f.default_factory()
                else:
                    val = f.default
                if is_dataclass(val):
                    # if val is a dataclass, convert to ConfigTree
                    val = ConfigFactory.from_dict(asdict(val))

            if val is not MISSING:
                fs[f.name] = __parse(
                    val, ftype, f"{path}.{f.name}", strict, ignore_unexpected
                )

            elif is_optional(ftype):
                # Optional not found
                fs[f.name] = None

            elif is_dataclass(ftype):
                nested_hints = _type_hints(ftype)
                nested_fields = [nf for nf in fields(ftype) if nf.init]
                if all(
                    field.default is not MISSING
                    or field.default_factory is not MISSING
                    or is_optional(nested_hints.get(field.name, field.type))
                    for field in nested_fields
                ):
                    fs[f.name] = ftype(
                        **{
                            field.name: None
                            for field in nested_fields
                            if is_optional(nested_hints.get(field.name, field.type))
                            and field.default is MISSING
                            and field.default_factory is MISSING
                        }
                    )
                else:
                    raise MalformedConfigException(
                        f'expected type {clazz} at {path_to_str(path)}, no field "{f.name}" found and {ftype} cannot be implicitly created'
                    )

            else:
                raise MalformedConfigException(
                    f'expected type {clazz} at {path_to_str(path)}, no field "{f.name}" found'
                )

        for name, f in getattr(clazz, "__dataclass_fields__", {}).items():
            if getattr(f, "_field_type", None) != dataclasses._FIELD_INITVAR:
                continue
            ftype = hints.get(name, f.type)
            if type(ftype).__name__ == "InitVar":
                ftype = getattr(ftype, "type", Any)
            if name in value:
                used_keys.add(name)
                fs[name] = __parse(
                    value[name], ftype, f"{path}.{name}", strict, ignore_unexpected
                )
            elif f.default is not MISSING or callable(f.default_factory):
                continue
            else:
                raise MalformedConfigException(
                    f'expected type {clazz} at {path_to_str(path)}, no field "{name}" found'
                )

        unexpected_keys = set(value.keys()) - used_keys
        if len(unexpected_keys) > 0 and not ignore_unexpected:
            raise UnexpectedKeysException(
                f'unexpected key(s) "{", ".join(map(str, unexpected_keys))}" detected for type {clazz} at {path_to_str(path)}'
            )

        return clazz(**fs)

    origin = get_origin(clazz)
    args = get_args(clazz)

    if clazz is list or origin is list:
        if len(args) != 1:
            raise MissingTypeException("expected list with type information: List[?]")

        parse_candidate = args[0]
        return [
            __parse(v, parse_candidate, f"{path}[]", strict, ignore_unexpected)
            for v in _sequence_from(value, path, list)
        ]

    if clazz is tuple:
        raise MissingTypeException("expected tuple with type information: Tuple[?]")

    if origin is tuple:
        seq = _sequence_from(value, path, tuple)
        if args == ():
            if len(seq) != 0:
                raise MalformedConfigException(
                    "number of provided values does not match expected number of values for tuple."
                )
            return ()

        if len(args) < 1:
            raise MissingTypeException("expected tuple with type information: Tuple[?]")

        has_ellipsis = args[-1] == Ellipsis
        if has_ellipsis and len(args) != 2:
            raise MissingTypeException(
                "expected one type since ellipsis is used: Tuple[?, ...]"
            )
        _args = args if not has_ellipsis else [args[0]] * len(seq)
        if len(seq) != len(_args):
            raise MalformedConfigException(
                "number of provided values does not match expected number of values for tuple."
            )
        return tuple(
            __parse(v, arg, f"{path}[]", strict, ignore_unexpected)
            for v, arg in zip(seq, _args)
        )

    if clazz is dict or origin is dict:
        if len(args) != 2:
            raise MissingTypeException(
                "expected dict with type information: Dict[?, ?]"
            )
        if value is None:
            raise MalformedConfigException(
                f"expected dict at {path_to_str(path)} but received None"
            )
        if not _is_mapping(value):
            raise TypeConfigException(
                f"expected type {clazz} at {path_to_str(path)}, got {type(value)}"
            )
        parse_candidate = args[1]
        return {
            k: __parse(v, parse_candidate, f"{path}.{k}", strict, ignore_unexpected)
            for k, v in value.items()
        }

    if is_union(origin):
        # Optional = Union[T, NoneType]
        has_none = False
        for parse_candidate in args:
            if parse_candidate is NoneType:
                has_none = True
            else:
                try:
                    return __parse(
                        value, parse_candidate, path, strict, ignore_unexpected
                    )
                except _UNION_CATCH:
                    continue

        if has_none and value is None:
            return None

        raise TypeConfigException(
            f"expected one of {', '.join(map(str, args))} at {path_to_str(path)}, got {type(value)}"
        )

    if clazz is bool:
        parsed = __parse_bool(value)
        if parsed is not None:
            return parsed
        return __parse_type(value, clazz, path, False)

    if clazz is int:
        if isinstance(value, bool):
            return __parse_type(value, clazz, path, False)
        if not strict and isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                pass
        return __parse_type(value, clazz, path, isinstance(value, int))

    if clazz is float:
        if isinstance(value, bool):
            return __parse_type(value, clazz, path, False)
        if not strict and isinstance(value, str):
            try:
                value = float(value)
            except ValueError:
                pass
        return __parse_type(value, clazz, path, isinstance(value, (float, int)))

    if clazz is str:
        return __parse_type(value, clazz, path, isinstance(value, str))

    if clazz is Any:
        return _plain(value)

    if isclass(clazz) and (issubclass(clazz, Enum) or issubclass(clazz, IntEnum)):
        if isinstance(value, clazz):
            return value
        try:
            if isinstance(value, int) and not isinstance(value, bool):
                return clazz(value)
            if isinstance(value, str):
                try:
                    return clazz[value]
                except KeyError:
                    return clazz(value)
        except (KeyError, ValueError):
            raise TypeConfigException(
                f"expected type {clazz} at {path_to_str(path)}, got {value!r}"
            )
        raise TypeConfigException(
            f"expected str or int at {path_to_str(path)}, got {type(value)}"
        )

    if isclass(clazz) and issubclass(clazz, Path):
        if isinstance(value, (str, Path)):
            return clazz(value)
        raise TypeConfigException(
            f"expected type {clazz} at {path_to_str(path)}, got {type(value)}"
        )

    if get_origin(clazz) is (Literal):
        if any(v == value and type(v) is type(value) for v in args):
            return value
        raise TypeConfigException(
            f"expected one of {', '.join(map(str, args))} at {path_to_str(path)}, got {value}"
        )

    if clazz is datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        dt = __parse_type(value, clazz, path, isinstance(value, str))
        try:
            return isoparse(dt)
        except ValueError as e:
            raise ParseException(
                f"expected type {clazz} at {path_to_str(path)}, cannot parse due to {e}"
            )

    if clazz is date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        dt = __parse_type(value, clazz, path, isinstance(value, str))
        try:
            return isoparse(dt).date()
        except ValueError as e:
            raise ParseException(
                f"expected type {clazz} at {path_to_str(path)}, cannot parse due to {e}"
            )

    if clazz is timedelta:
        if isinstance(value, timedelta) and not isinstance(value, relativedelta):
            return value
        if isinstance(value, relativedelta):
            if value.years or value.months:
                raise ParseException(
                    "The ISO 8601 duration provided can not contain years or months"
                )
            return timedelta(
                days=value.days,
                hours=value.hours,
                minutes=value.minutes,
                seconds=value.seconds,
                microseconds=value.microseconds,
            )
        dt = __parse_type(value, clazz, path, isinstance(value, str))
        try:
            duration = parse_duration(dt)
            if isinstance(duration, Duration):
                raise ParseException(
                    "The ISO 8601 duration provided can not contain years or months"
                )
            return duration
        except ValueError as e:
            raise ParseException(
                f"expected type {clazz} at {path_to_str(path)}, cannot parse due to {e}"
            )

    if clazz is bytes:
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode()
        raise TypeConfigException(
            f"expected type {clazz} at {path_to_str(path)}, got {type(value)}"
        )

    if clazz is UUID:
        if isinstance(value, UUID):
            return value
        if isinstance(value, str):
            try:
                return UUID(value)
            except ValueError as e:
                raise ParseException(
                    f"expected type {clazz} at {path_to_str(path)}, cannot parse due to {e}"
                )
        raise TypeConfigException(
            f"expected type {clazz} at {path_to_str(path)}, got {type(value)}"
        )

    if clazz is relativedelta:
        if isinstance(value, relativedelta):
            return value
        dt = __parse_type(value, clazz, path, isinstance(value, str))
        try:
            duration = parse_duration(dt)
        except ValueError as e:
            raise ParseException(
                f"expected type {clazz} at {path_to_str(path)}, cannot parse due to {e}"
            )
        if isinstance(duration, Duration):
            extra = duration.tdelta
            return relativedelta(
                years=int(duration.years or 0),
                months=int(duration.months or 0),
                days=extra.days,
                seconds=extra.seconds,
                microseconds=extra.microseconds,
            )
        return relativedelta(
            days=duration.days,
            seconds=duration.seconds,
            microseconds=duration.microseconds,
        )

    child_failures = []
    child_successes = []
    if not _is_mapping(value):
        raise TypeConfigException(
            f"expected type {clazz} at {path_to_str(path)}, got {type(value)}"
        )
    try:
        subtype = value.pop("_type", default=None)
    except TypeError:
        subtype = value.pop("_type", None)
    for child_clazz in sorted(clazz.__subclasses__(), key=lambda c: c.__name__):
        if is_dataclass(child_clazz) and (
            subtype is None
            or f"{child_clazz.__module__}.{child_clazz.__name__}".endswith(subtype)
        ):
            try:
                child_successes.append(
                    (
                        child_clazz,
                        __parse(value, child_clazz, path, strict, ignore_unexpected),
                    )
                )
            except (
                TypeConfigException,
                MalformedConfigException,
                UnexpectedKeysException,
                AmbiguousSubclassException,
            ) as e:
                child_failures.append(e)

    if len(child_successes) == 1:
        return child_successes[0][1]
    elif len(child_successes) > 1:
        matching_classes = "\n- ".join(x[0].__name__ for x in child_successes)
        raise AmbiguousSubclassException(
            f"""multiple subtypes of {clazz} matched at {path_to_str(path)}, use '_type' to disambiguate:\n- {matching_classes}"""
        )

    # no need to check length; false if empty
    if child_failures:
        failures = "\n- ".join([str(c) for c in child_failures])
        raise TypeConfigException(
            f"expected type {clazz} at {path_to_str(path)}, failed subclasses:\n- {failures}"
        )

    raise TypeConfigException(
        f"expected type {clazz} at {path_to_str(path)}, got {type(value)}"
    )


def __generate(value: object, path: str):
    if is_dataclass(value):
        tree = {k: __generate(v, f"{path}.{k}") for k, v in asdict(value).items()}
        return ConfigTree(tree)

    if isinstance(value, dict):
        tree = {k: __generate(v, f"{path}.{k}") for k, v in value.items()}
        return ConfigTree(tree)

    if isinstance(value, (list, tuple)):
        tree = [__generate(e, f"{path}[]") for e in value]
        return ConfigList(tree)

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, Enum):
        return __generate(value.value, path)

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, relativedelta):
        return _relativedelta_iso(value)

    if isinstance(value, timedelta):
        return duration_isoformat(value)

    if isinstance(value, UUID):
        return str(value)

    return value


def __to_toml(value: object):
    if isinstance(value, (ConfigTree, dict)):
        out = {}
        for k, v in value.items():
            converted = __to_toml(v)
            if converted is not None:
                out[str(k)] = converted
        return out

    if isinstance(value, (list, tuple, ConfigList)):
        encoded = []
        for v in value:
            if v is None:
                raise ParseException("TOML cannot encode null list items")
            encoded.append(__to_toml(v))
        return encoded

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, Enum):
        return __to_toml(value.value)

    if isinstance(value, relativedelta):
        return _relativedelta_iso(value)

    if isinstance(value, timedelta):
        return duration_isoformat(value)

    return value


def __env_vars_parse(prefix: str, obj: dict[str, Any]):
    ret = {}

    def set_lens(p, focus, v):
        # value
        if len(p) == 1:
            # []x
            if isinstance(focus, list):
                if not isinstance(p[0], int):
                    raise EnvListFormatException
                if p[0] != len(focus):
                    raise EnvListOrderException
                focus.append(v)
            # {}x
            else:
                key = str(p[0]) if isinstance(p[0], int) else p[0]
                focus[key] = v
            return

        # dict
        if p[1] == "":
            if not _has_index(focus, p[0]):
                # []{x}
                if isinstance(focus, list):
                    if p[0] != len(focus):
                        raise EnvListOrderException
                    focus.append({})
                # {}{x}
                else:
                    focus[p[0]] = {}
            elif not isinstance(focus[p[0]], (dict, list)):
                raise ParseException(
                    f"cannot nest under {p[0]!r}: existing value is {type(focus[p[0]])}"
                )

            if len(p) == 2:
                focus[p[0]] = v
                return
            return set_lens(p[2:], focus[p[0]], v)

        # list (only if the focus/value is already a list or if it starts with element 0)
        parent_is_list = _has_index(focus, p[0]) and isinstance(focus[p[0]], list)
        if isinstance(p[1], int) and (p[1] == 0 or parent_is_list):
            if not _has_index(focus, p[0]):
                # [][x]
                if isinstance(focus, list):
                    if p[0] != len(focus):
                        raise EnvListOrderException
                    focus.append([])
                # {}[x]
                else:
                    focus[p[0]] = []

            return set_lens(p[1:], focus[p[0]], v)

        # compose path
        return set_lens([f"{p[0]}_{p[1]}"] + p[2:], focus, v)

    def int_or_string(v):
        try:
            return int(v)
        except ValueError:
            return v

    if not prefix.endswith("_") and prefix != "":
        prefix = f"{prefix}_"

    def _env_sort_key(k: str):
        return tuple(
            int(part) if part.isdigit() else part for part in _ENV_KEY_PARTS.split(k)
        )

    for k, v in sorted(obj.items(), key=lambda x: _env_sort_key(x[0])):
        if k.startswith(prefix):
            if k.endswith("_"):
                try:
                    v = ConfigFactory.parse_string(v)
                except pyparsing.ParseBaseException as e:
                    raise ParseException(
                        f"env var {k} ends with `_` and expects a nested config, got: {e}"
                    )
                k = k[:-1]

            path = [int_or_string(e) for e in k[len(prefix) :].lower().split("_")]
            set_lens(path, ret, v)

    return ret


def path_to_str(path: str) -> str:
    return path if len(path) > 0 else "root"


def __cli_parse(argv: list[str]):
    kvs = {}
    i = 0

    if argv and not argv[0].startswith("--"):
        i += 1

    while i < len(argv):
        curr = argv[i]
        if not curr.startswith("--"):
            raise ParseException(f"cli argument {curr} is misplaced")

        if i + 1 == len(argv):
            raise ParseException("last argument is missing")

        kvs[curr[2:].replace("-", "_")] = argv[i + 1]
        i += 2

    return __env_vars_parse("", kvs)
