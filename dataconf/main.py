import os
from typing import List

from dataconf import utils
from dataconf.exceptions import MalformedConfigException
from pyhocon import ConfigFactory
from pyhocon import HOCONConverter
from pyhocon.config_parser import ConfigTree
import pyparsing


def parse(
    conf: ConfigTree, clazz, strict: bool = True, ignore_unexpected: bool = False
):
    try:
        return utils.__parse(conf, clazz, "", strict, ignore_unexpected)
    except pyparsing.ParseSyntaxException as e:
        raise MalformedConfigException(
            f'parsing failure line {e.lineno} character {e.col}, got "{e.line}"'
        )


def env_dict_list(prefix: str):
    return utils.__dict_list_parsing(prefix, os.environ)


class Multi:
    def __init__(self, confs: List[ConfigTree], strict: bool = True, **kwargs) -> None:
        self.confs = confs
        self.strict = strict
        self.kwargs = kwargs

    def env(self, prefix: str, **kwargs) -> "Multi":
        self.strict = False
        return self.dict(env_dict_list(prefix), **kwargs)

    def dict(self, obj: str, **kwargs) -> "Multi":
        conf = ConfigFactory.from_dict(obj)
        return Multi(self.confs + [conf], self.strict, **kwargs)

    def string(self, s: str, **kwargs) -> "Multi":
        conf = ConfigFactory.parse_string(s)
        return Multi(self.confs + [conf], self.strict, **kwargs)

    def url(self, uri: str, **kwargs) -> "Multi":
        conf = ConfigFactory.parse_URL(uri)
        return Multi(self.confs + [conf], self.strict, **kwargs)

    def file(self, path: str, **kwargs) -> "Multi":
        conf = ConfigFactory.parse_file(path)
        return Multi(self.confs + [conf], self.strict, **kwargs)

    def on(self, clazz):
        conf, *nxts = self.confs
        for nxt in nxts:
            conf = ConfigTree.merge_configs(conf, nxt)
        return parse(conf, clazz, self.strict, **self.kwargs)


multi = Multi([])


def env(prefix: str, clazz, **kwargs):
    return multi.env(prefix, **kwargs).on(clazz)


def dict(obj: str, clazz, **kwargs):
    return multi.dict(obj, **kwargs).on(clazz)


def string(s: str, clazz, **kwargs):
    return multi.string(s, **kwargs).on(clazz)


def url(uri: str, clazz, **kwargs):
    return multi.url(uri, **kwargs).on(clazz)


def file(path: str, clazz, **kwargs):
    return multi.file(path, **kwargs).on(clazz)


def load(path: str, clazz, **kwargs):
    return file(path, clazz, **kwargs)


def loads(s: str, clazz, **kwargs):
    return string(s, clazz, **kwargs)


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
