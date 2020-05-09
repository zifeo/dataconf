from dataclasses import asdict
from dataclasses import fields
from dataclasses import is_dataclass
from datetime import timedelta
from typing import get_args
from typing import get_origin
from typing import Union

from dataconf.exceptions import MalformedConfigException
from dataconf.exceptions import TypeConfigException
from pyhocon import ConfigFactory
from pyhocon import HOCONConverter
from pyhocon.config_tree import ConfigList
from pyhocon.config_tree import ConfigTree
from pyhocon.exceptions import ConfigMissingException
import pyparsing

NoneType = type(None)


def __parse_type(value, clazz, path, check):
    try:
        if check:
            return value
    except TypeError:
        pass

    raise TypeConfigException(f"expected type {clazz} at {path}, got {type(value)}")


def __parse(value: any, clazz, path):

    if is_dataclass(clazz):

        if not isinstance(value, ConfigTree):
            raise TypeConfigException(
                f"expected type {clazz} at {path}, got {type(value)}"
            )

        fs = {}

        for f in fields(clazz):
            try:
                val = value[f.name]
            except ConfigMissingException:
                if callable(f.default):
                    val = f.default()
                else:
                    val = None
            fs[f.name] = __parse(val, f.type, f"{path}.{f.name}")

        return clazz(**fs)

    origin = get_origin(clazz)
    args = get_args(clazz)

    if origin is list:
        return [__parse(v, args[0], f"{path}[]") for v in value]

    if origin is dict:
        return {k: __parse(v, args[1], f"{path}.{k}") for k, v in value.items()}

    if origin is Union:
        left, right = args

        try:
            return __parse(value, left, path)
        except TypeConfigException as left_failure:
            # Optional = Union[T, NoneType]
            if right is NoneType:
                return None

            try:
                return __parse(value, right, path)
            except TypeConfigException as right_failure:
                raise TypeConfigException(
                    f"expected type {clazz} at {path}, failed both:\n- {left_failure}\n- {right_failure}"
                )

    if clazz is int:
        return __parse_type(value, clazz, path, isinstance(value, int))

    if clazz is float:
        return __parse_type(value, clazz, path, isinstance(value, float))

    if clazz is str:
        return __parse_type(value, clazz, path, isinstance(value, str))

    if clazz is timedelta:
        return __parse_type(value, clazz, path, isinstance(value, timedelta))

    if clazz is ConfigTree:
        return __parse_type(value, clazz, path, isinstance(value, ConfigTree))

    raise TypeConfigException(f"expected type {clazz} at {path}, got {type(value)}")


def __generate(value: object, path):

    if is_dataclass(value):
        tree = {k: __generate(v, f"{path}.{k}") for k, v in asdict(value).items()}
        return ConfigTree(tree)

    if isinstance(value, dict):
        tree = {k: __generate(v, f"{path}.{k}") for k, v in value.items()}
        return ConfigTree(tree)

    if isinstance(value, list):
        tree = [__generate(e, f"{path}[]") for e in value]
        return ConfigList(tree)

    if isinstance(value, timedelta):
        ret = ""
        if value.days > 0:
            ret += f"{value.days}d "
        if value.seconds > 0:
            ret += f"{value.seconds}s "
        if value.microseconds > 0:
            ret += f"{value.microseconds}us "
        return ret.strip()

    return value


def load(file: str, clazz):
    try:
        conf = ConfigFactory.parse_file(file)
        return __parse(conf, clazz, "")
    except pyparsing.ParseSyntaxException as e:
        raise MalformedConfigException(
            f'parsing failure line {e.lineno} character {e.col}, got "{e.line}"'
        )


def loads(string: str, clazz):
    try:
        conf = ConfigFactory.parse_string(string)
        return __parse(conf, clazz, "")
    except pyparsing.ParseSyntaxException as e:
        raise MalformedConfigException(
            f'parsing failure line {e.lineno} character {e.col}, got "{e.line}"'
        )


def dump(file: str, instance: object, out: str):
    with open(file, "w") as f:
        f.write(dumps(instance, out=out))


def dumps(instance: object, out: str):
    conf = __generate(instance, "")

    if out:
        if out.lower() == "hocon":
            return HOCONConverter.to_hocon(conf)
        if out.lower() == "yaml":
            return HOCONConverter.to_yaml(conf)
        if out.lower() == "json":
            return HOCONConverter.to_json(conf)
        if out.lower() == "properties":
            return HOCONConverter.to_properties(conf)

    return conf
