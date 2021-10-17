import os

from dataconf import utils
from dataconf.exceptions import MalformedConfigException
from pyhocon import ConfigFactory
from pyhocon import HOCONConverter
import pyparsing


def __parse_config_tree(conf, clazz):
    try:
        return utils.__parse(conf, clazz, "")
    except pyparsing.ParseSyntaxException as e:
        raise MalformedConfigException(
            f'parsing failure line {e.lineno} character {e.col}, got "{e.line}"'
        )


def env(prefix: str, clazz):
    conf = ConfigFactory.from_dict(utils.__dict_list_parsing(prefix, os.environ))
    return __parse_config_tree(conf, clazz)


def string(s: str, clazz):
    conf = ConfigFactory.parse_string(s)
    return __parse_config_tree(conf, clazz)


def url(uri: str, clazz):
    conf = ConfigFactory.parse_URL(uri)
    return __parse_config_tree(conf, clazz)


def file(path: str, clazz):
    conf = ConfigFactory.parse_file(path)
    return __parse_config_tree(conf, clazz)


def load(path: str, clazz):
    return file(path, clazz)


def loads(s: str, clazz):
    return string(s, clazz)


def dump(file: str, instance: object, out: str):
    with open(file, "w") as f:
        f.write(dumps(instance, out=out))


def dumps(instance: object, out: str):
    conf = utils.__generate(instance, "")

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
