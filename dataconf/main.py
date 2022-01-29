import os
from typing import List

from dataconf import utils
from dataconf.exceptions import MalformedConfigException
from pyhocon import ConfigFactory
from pyhocon import HOCONConverter
from pyhocon.config_parser import ConfigTree
import pyparsing


def parse(conf: ConfigTree, clazz, strict=True):
    try:
        return utils.__parse(conf, clazz, "", strict)
    except pyparsing.ParseSyntaxException as e:
        raise MalformedConfigException(
            f'parsing failure line {e.lineno} character {e.col}, got "{e.line}"'
        )


def env_dict_list(prefix: str):
    return utils.__dict_list_parsing(prefix, os.environ)


class Multi:
    def __init__(self, confs: List[ConfigTree], strict: bool = True) -> None:
        self.confs = confs
        self.strict = strict

    def env(self, prefix: str) -> "Multi":
        self.strict = False
        return self.dict(env_dict_list(prefix))

    def dict(self, obj: str) -> "Multi":
        conf = ConfigFactory.from_dict(obj)
        return Multi(self.confs + [conf], self.strict)

    def string(self, s: str) -> "Multi":
        conf = ConfigFactory.parse_string(s)
        return Multi(self.confs + [conf], self.strict)

    def url(self, uri: str) -> "Multi":
        conf = ConfigFactory.parse_URL(uri)
        return Multi(self.confs + [conf], self.strict)

    def file(self, path: str) -> "Multi":
        conf = ConfigFactory.parse_file(path)
        return Multi(self.confs + [conf], self.strict)

    def on(self, clazz):
        conf, *nxts = self.confs
        for nxt in nxts:
            conf = ConfigTree.merge_configs(conf, nxt)
        return parse(conf, clazz, self.strict)


multi = Multi([])


def env(prefix: str, clazz):
    return multi.env(prefix).on(clazz)


def dict(obj: str, clazz):
    return multi.dict(obj).on(clazz)


def string(s: str, clazz):
    return multi.string(s).on(clazz)


def url(uri: str, clazz):
    return multi.url(uri).on(clazz)


def file(path: str, clazz):
    return multi.file(path).on(clazz)


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
