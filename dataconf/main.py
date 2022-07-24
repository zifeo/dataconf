import inspect
import os
from typing import List
from typing import Type

from dataconf import utils
from dataconf.exceptions import MalformedConfigException
from pyhocon import ConfigFactory
from pyhocon import HOCONConverter
from pyhocon.config_parser import ConfigTree
import pyparsing


def inject_callee_scope(func):
    def inner(*args, **kwargs):
        noglobals = "globalns" not in kwargs
        nolocals = "localns" not in kwargs

        if noglobals or nolocals:
            frame = inspect.stack()[1][0]

            if noglobals:
                kwargs["globalns"] = frame.f_globals
            if nolocals:
                kwargs["localns"] = frame.f_locals

        return func(
            *args,
            **kwargs,
        )

    return inner


@inject_callee_scope
def parse(
    conf: ConfigTree,
    clazz,
    strict: bool = True,
    ignore_unexpected: bool = False,
    globalns=None,
    localns=None,
):

    try:
        return utils.__parse(
            conf, clazz, "", strict, ignore_unexpected, globalns, localns
        )
    except pyparsing.ParseSyntaxException as e:
        raise MalformedConfigException(
            f'parsing failure line {e.lineno} character {e.col}, got "{e.line}"'
        )


def env_vars_parse(*args, **kwargs):
    return utils.__env_vars_parse(*args, **kwargs)


def cli_parse(*args, **kwargs):
    return utils.__cli_parse(*args, **kwargs)


class Multi:
    def __init__(self, confs: List[ConfigTree], strict: bool = True) -> None:
        self.confs = confs
        self.strict = strict

    def env(self, prefix: str) -> "Multi":
        self.strict = False
        data = env_vars_parse(prefix, os.environ)
        return self.dict(data)

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

    def cli(self, argv: List[str]) -> "Multi":
        data = cli_parse(argv)
        return self.dict(data)

    @inject_callee_scope
    def on(self, clazz: Type, **kwargs):
        conf, *nxts = self.confs
        for nxt in nxts:
            conf = ConfigTree.merge_configs(conf, nxt)
        return parse(conf, clazz, self.strict, **kwargs)


multi = Multi([])


@inject_callee_scope
def env(prefix: str, clazz: Type, **kwargs):
    return multi.env(prefix).on(clazz, **kwargs)


@inject_callee_scope
def dict(obj: str, clazz: Type, **kwargs):
    return multi.dict(obj).on(clazz, **kwargs)


@inject_callee_scope
def string(s: str, clazz: Type, **kwargs):
    return multi.string(s).on(clazz, **kwargs)


@inject_callee_scope
def url(uri: str, clazz: Type, **kwargs):
    return multi.url(uri).on(clazz, **kwargs)


@inject_callee_scope
def file(path: str, clazz: Type, **kwargs):
    return multi.file(path).on(clazz, **kwargs)


@inject_callee_scope
def cli(argv: List[str], clazz: Type, **kwargs):
    return multi.cli(argv).on(clazz, **kwargs)


@inject_callee_scope
def load(path: str, clazz: Type, **kwargs):
    return file(path, clazz, **kwargs)


@inject_callee_scope
def loads(s: str, clazz: Type, **kwargs):
    return string(s, clazz, **kwargs)


def dump(file: str, instance: object, out: str):
    with open(file, "w") as f:
        f.write(dumps(instance, out=out))


def dumps(instance: object, out: str):
    conf = utils.generate(instance, "")

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
