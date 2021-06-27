from dataclasses import asdict
from dataclasses import fields
from dataclasses import is_dataclass
from typing import get_args
from typing import get_origin
from typing import Union

from dataconf.exceptions import MalformedConfigException
from dataconf.exceptions import MissingTypeException
from dataconf.exceptions import TypeConfigException
from dateutil.relativedelta import relativedelta
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
                if callable(f.default_factory):
                    val = f.default_factory()
                else:
                    val = f.default
            fs[f.name] = __parse(val, f.type, f"{path}.{f.name}")

        return clazz(**fs)

    origin = get_origin(clazz)
    args = get_args(clazz)

    if origin is list:
        if len(args) != 1:
            raise MissingTypeException("excepted list with type information: List[?]")
        return [__parse(v, args[0], f"{path}[]") for v in value]

    if origin is dict:
        if len(args) != 2:
            raise MissingTypeException(
                "excepted dict with type information: Dict[?, ?]"
            )
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

    if clazz is bool:
        return __parse_type(value, clazz, path, isinstance(value, bool))

    if clazz is int:
        return __parse_type(value, clazz, path, isinstance(value, int))

    if clazz is float:
        return __parse_type(value, clazz, path, isinstance(value, float))

    if clazz is str:
        return __parse_type(value, clazz, path, isinstance(value, str))

    if clazz is relativedelta:
        return __parse_type(value, clazz, path, isinstance(value, relativedelta))

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

    # needs a better impl.
    # if isinstance(value, timedelta):
    # if isinstance(value, relativedelta):

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
