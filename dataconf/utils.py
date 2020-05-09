from pyhocon import ConfigFactory
from pyhocon.config_tree import ConfigTree
from pyhocon.exceptions import ConfigMissingException
from dataclasses import is_dataclass, fields, _MISSING_TYPE
from typing import get_origin, get_args, Union, Optional
from dataconf.exceptions import TypeConfigException, MalformedConfigException
import pyparsing
from datetime import timedelta

NoneType = type(None)

def __parse_type(value, clazz, path, check):
    try:
        if check:
            return value
    except TypeError:
        pass

    raise TypeConfigException(f'expected type {clazz} at {path}, got {type(value)}')


def __parse(value: any, clazz, path):

    if is_dataclass(clazz):

        if not isinstance(value, ConfigTree):
            raise TypeConfigException(f'expected type {clazz} at {path}, got {type(value)}')

        fs = {}

        for f in fields(clazz):
            try:
                val = value[f.name]
            except ConfigMissingException:
                if callable(f.default):
                    val = f.default()
                else:
                    val = None
            fs[f.name] = __parse(val, f.type, f'{path}.{f.name}')

        return clazz(**fs)

    origin = get_origin(clazz)
    args = get_args(clazz)

    if origin is list:
        return [__parse(v, args[0], f'{path}[]') for v in value]

    if origin is dict:
        return {k: __parse(v, args[1], f'{path}.{k}') for k, v in value.items()}

    if origin is Union:
        left, right = args

        try:
            return __parse(value, left, path)
        except TypeConfigException as left_failure:
            if right is NoneType:
                return None

            try:
                return __parse(value, right, path)
            except TypeConfigException as right_failure:
                raise TypeConfigException(f'expected type {clazz} at {path}, failed both:\n- {left_failure}\n- {right_failure}')

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

    raise TypeConfigException(f'expected type {clazz} at {path}, got {type(value)}')


def load(file: str, clazz):
    try:
        conf = ConfigFactory.parse_file(file)
        return __parse(conf, clazz, '')
    except pyparsing.ParseSyntaxException as e:
        raise MalformedConfigException(f'parsing failure line {e.lineno} character {e.col}, got "{e.line}"')


def loads(string: str, clazz):
    try:
        conf = ConfigFactory.parse_string(string)
        return __parse(conf, clazz, '')
    except pyparsing.ParseSyntaxException as e:
        raise MalformedConfigException(f'parsing failure line {e.lineno} character {e.col}, got "{e.line}"')



def dump(file: str, instance):
    return None


def dumps(string: str, clazz):
    return ""


