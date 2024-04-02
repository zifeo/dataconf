from dataclasses import _MISSING_TYPE
from dataclasses import asdict
from dataclasses import fields
from dataclasses import is_dataclass
from datetime import datetime
from datetime import timedelta
from enum import Enum
from enum import IntEnum
from inspect import isclass
from pathlib import Path

from typing import Any, Literal
from typing import Dict
from typing import get_args
from typing import get_origin
from typing import List
from typing import Type
from typing import Union

from dataconf.exceptions import AmbiguousSubclassException
from dataconf.exceptions import EnvListOrderException
from dataconf.exceptions import MalformedConfigException
from dataconf.exceptions import MissingTypeException
from dataconf.exceptions import ParseException
from dataconf.exceptions import TypeConfigException
from dataconf.exceptions import UnexpectedKeysException
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
from pyhocon import ConfigFactory
from pyhocon.config_tree import ConfigList
from pyhocon.config_tree import ConfigTree
from isodate import parse_duration
from isodate import Duration
import pyparsing

from dataconf.version import PY310up


if PY310up:
    from types import UnionType


NoneType = type(None)


def __parse_type(value: Any, clazz: Type, path: str, check: bool):
    try:
        if check:
            return value
    except TypeError:
        pass

    raise TypeConfigException(f"expected type {clazz} at {path}, got {type(value)}")


def is_union(origin):
    return origin is Union or (PY310up and origin is UnionType)


def is_optional(type: Type):
    # Optional = Union[T, NoneType]
    return is_union(get_origin(type)) and NoneType in get_args(type)


def __parse(value: any, clazz: Type, path: str, strict: bool, ignore_unexpected: bool):
    if is_dataclass(clazz):
        if not isinstance(value, ConfigTree):
            raise TypeConfigException(
                f"expected type {clazz} at {path}, got {type(value)}"
            )

        fs = {}
        renamings = dict()

        for f in fields(clazz):
            if f.name in value:
                val = value[f.name]
            elif f.name.replace("_", "-") in value:
                renamings[f.name] = f.name.replace("_", "-")
                val = value[f.name.replace("_", "-")]
            else:
                if callable(f.default_factory):
                    val = f.default_factory()
                else:
                    val = f.default
                if is_dataclass(val):
                    # if val is a dataclass, convert to ConfigTree
                    val = ConfigTree(asdict(val))

            if not isinstance(val, _MISSING_TYPE):
                fs[f.name] = __parse(
                    val, f.type, f"{path}.{f.name}", strict, ignore_unexpected
                )

            elif is_optional(f.type):
                # Optional not found
                fs[f.name] = None

            else:
                raise MalformedConfigException(
                    f"expected type {clazz} at {path}, no {f.name} found in dataclass"
                )

        unexpected_keys = value.keys() - {renamings.get(k, k) for k in fs.keys()}
        if len(unexpected_keys) > 0 and not ignore_unexpected:
            raise UnexpectedKeysException(
                f"unexpected key(s) \"{', '.join(unexpected_keys)}\" detected for type {clazz} at {path}"
            )

        return clazz(**fs)

    origin = get_origin(clazz)
    args = get_args(clazz)

    if origin is list:
        if value is None:
            raise MalformedConfigException(f"expected list at {path} but received None")

        if len(args) != 1:
            raise MissingTypeException("expected list with type information: List[?]")

        parse_candidate = args[0]
        return [
            __parse(v, parse_candidate, f"{path}[]", strict, ignore_unexpected)
            for v in value
        ]

    if origin is tuple:
        if value is None:
            raise MalformedConfigException(
                f"expected tuple at {path} but received None"
            )

        if len(args) < 1:
            raise MissingTypeException("expected tuple with type information: Tuple[?]")

        has_ellipsis = args[-1] == Ellipsis
        if has_ellipsis and len(args) != 2:
            raise MissingTypeException(
                "expected one type since ellipsis is used: Tuple[?, ...]"
            )
        _args = args if not has_ellipsis else [args[0]] * len(value)
        if len(value) > 0 and len(value) != len(_args):
            raise MalformedConfigException(
                "number of provided values does not match expected number of values for tuple."
            )
        return tuple(
            __parse(v, arg, f"{path}[]", strict, ignore_unexpected)
            for v, arg in zip(value, _args)
        )

    if origin is dict:
        if len(args) != 2:
            raise MissingTypeException(
                "expected dict with type information: Dict[?, ?]"
            )
        if value is not None:
            # ignore key type
            parse_candidate = args[1]
            return {
                k: __parse(v, parse_candidate, f"{path}.{k}", strict, ignore_unexpected)
                for k, v in value.items()
            }
        return None

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
                except TypeConfigException:
                    continue

        if has_none:
            return None

        raise TypeConfigException(
            f"expected one of {', '.join(map(str, args))} at {path}, got {type(value)}"
        )

    if clazz is bool:
        if not strict and value is not None:
            try:
                value = bool(value)
            except ValueError:
                pass
        return __parse_type(value, clazz, path, isinstance(value, bool))

    if clazz is int:
        if not strict and value is not None:
            try:
                value = int(value)
            except ValueError:
                pass
        return __parse_type(value, clazz, path, isinstance(value, int))

    if clazz is float:
        if not strict and value is not None:
            try:
                value = float(value)
            except ValueError:
                pass
        return __parse_type(
            value, clazz, path, isinstance(value, float) or isinstance(value, int)
        )

    if clazz is str:
        return __parse_type(value, clazz, path, isinstance(value, str))

    if clazz is Any:
        if type(value) is ConfigTree:
            return dict(value)

        return value

    if isclass(clazz) and (issubclass(clazz, Enum) or issubclass(clazz, IntEnum)):
        if isinstance(value, int):
            return clazz.__call__(value)
        elif issubclass(clazz, str):
            return clazz(value)
        elif isinstance(value, str):
            return clazz.__getitem__(value)
        raise TypeConfigException(f"expected str or int at {path}, got {type(value)}")

    if isclass(clazz) and issubclass(clazz, Path):
        return clazz.__call__(value)

    if get_origin(clazz) is (Literal):
        if value in args:
            return value
        raise TypeConfigException(
            f"expected one of {', '.join(map(str, args))} at {path}, got {value}"
        )

    if clazz is datetime:
        dt = __parse_type(value, clazz, path, isinstance(value, str))
        try:
            return isoparse(dt)
        except ValueError as e:
            raise ParseException(
                f"expected type {clazz} at {path}, cannot parse due to {e}"
            )

    if clazz is timedelta:
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
                f"expected type {clazz} at {path}, cannot parse due to {e}"
            )

    if clazz is relativedelta:
        return __parse_type(value, clazz, path, isinstance(value, relativedelta))

    child_failures = []
    child_successes = []
    subtype = value.pop("_type", default=None)
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
        matching_classes = "\n- ".join(map(lambda x: x[0].__name__, child_successes))
        raise AmbiguousSubclassException(
            f"""multiple subtypes of {clazz} matched at {path}, use '_type' to disambiguate:\n- {matching_classes}"""
        )

    # no need to check length; false if empty
    if child_failures:
        failures = "\n- ".join([str(c) for c in child_failures])
        raise TypeConfigException(
            f"expected type {clazz} at {path}, failed subclasses:\n- {failures}"
        )

    raise TypeConfigException(f"expected type {clazz} at {path}, got {type(value)}")


def __generate(value: object, path: str):
    if is_dataclass(value):
        tree = {k: __generate(v, f"{path}.{k}") for k, v in asdict(value).items()}
        return ConfigTree(tree)

    if isinstance(value, dict):
        tree = {k: __generate(v, f"{path}.{k}") for k, v in value.items()}
        return ConfigTree(tree)

    if isinstance(value, list):
        tree = [__generate(e, f"{path}[]") for e in value]
        return ConfigList(tree)

    # needs a better impl.
    # if isinstance(value, timedelta):
    # if isinstance(value, relativedelta):

    return value


def __env_vars_parse(prefix: str, obj: Dict[str, Any]):
    ret = {}

    def set_lens(p, focus, v):
        # value
        if len(p) == 1:
            # []x
            if isinstance(focus, list):
                if p[0] != len(focus):
                    raise EnvListOrderException
                focus.append(v)
            # {}x
            else:
                focus[p[0]] = v
            return

        # dict
        if p[1] == "":
            if p[0] not in focus:
                # []{x}
                if isinstance(focus, list):
                    if p[0] != len(focus):
                        raise EnvListOrderException
                    focus.append({})
                # {}{x}
                else:
                    focus[p[0]] = {}

            return set_lens(p[2:], focus[p[0]], v)

        # list (only if the focus/value is already a list or if it starts with element 0)
        if isinstance(p[1], int) and (p[1] == 0 or isinstance(focus[p[0]], list)):
            if p[0] not in focus:
                # [][x]
                if isinstance(focus, list):
                    if p[1] != len(focus):
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

    for k, v in sorted(obj.items(), key=lambda x: x[0]):
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


def __cli_parse(argv: List[str]):
    kvs = {}
    i = 0

    if not argv[0].startswith("--"):
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
