import contextlib
import os
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen

import pyparsing
import tomli_w
from pyhocon import ConfigFactory
from pyhocon import HOCONConverter
from pyhocon.config_parser import ConfigTree
from yaml import safe_load

from dataconf import utils
from dataconf.exceptions import MalformedConfigException
from dataconf.version import PY311up

if PY311up:
    import tomllib
else:
    import tomli as tomllib

HOCON = 1
YAML = 2
TOML = 3


def parse(
    conf: ConfigTree, clazz, strict: bool = True, ignore_unexpected: bool = False
):
    try:
        return utils.__parse(conf, clazz, "", strict, ignore_unexpected)
    except pyparsing.ParseSyntaxException as e:
        raise MalformedConfigException(
            f'parsing failure line {e.lineno} character {e.col}, got "{e.line}"'
        )


def env_vars_parse(*args, **kwargs):
    return utils.__env_vars_parse(*args, **kwargs)


def cli_parse(*args, **kwargs):
    return utils.__cli_parse(*args, **kwargs)


class Multi:
    def __init__(self, confs: list[ConfigTree], strict: bool = True, **kwargs) -> None:
        self.confs = confs
        self.strict = strict
        self.kwargs = kwargs

    def env(self, prefix: str, **kwargs) -> "Multi":
        data = env_vars_parse(prefix, os.environ)
        strict = kwargs.pop("strict", False)
        return self.dict(data, strict=strict, **kwargs)

    def dict(self, obj: dict[str, Any], **kwargs) -> "Multi":
        conf = ConfigFactory.from_dict(obj)
        strict = kwargs.pop("strict", self.strict)
        return Multi(self.confs + [conf], strict, **kwargs)

    def string(self, s: str, loader: str = HOCON, **kwargs) -> "Multi":
        if loader == YAML:
            data = safe_load(s)
            return self.dict(data, **kwargs)

        if loader == TOML:
            data = tomllib.loads(s)
            return self.dict(data, **kwargs)

        conf = ConfigFactory.parse_string(s)
        return Multi(self.confs + [conf], self.strict, **kwargs)

    def url(self, uri: str, timeout: int = 10, **kwargs) -> "Multi":
        path = urlparse(uri).path
        if path.endswith((".yaml", ".yml")):
            with contextlib.closing(urlopen(uri, timeout=timeout)) as fd:
                s = fd.read().decode("utf-8")
            return self.string(s, loader=YAML, **kwargs)

        if path.endswith(".toml"):
            with contextlib.closing(urlopen(uri, timeout=timeout)) as fd:
                s = fd.read().decode("utf-8")
            return self.string(s, loader=TOML, **kwargs)

        conf = ConfigFactory.parse_URL(uri, timeout=timeout, required=True)
        return Multi(self.confs + [conf], self.strict, **kwargs)

    def file(
        self,
        path: str,
        loader: str | None = None,
        allow_missing: bool = False,
        **kwargs,
    ) -> "Multi":
        if allow_missing and not os.path.exists(path):
            return self.dict({}, **kwargs)

        if loader == YAML or (loader is None and path.endswith((".yaml", ".yml"))):
            with open(path, "r") as f:
                data = safe_load(f)
            return self.dict(data, **kwargs)

        if loader == TOML or (loader is None and path.endswith(".toml")):
            with open(path, "rb") as f:
                data = tomllib.load(f)
            return self.dict(data, **kwargs)

        conf = ConfigFactory.parse_file(path)
        return Multi(self.confs + [conf], self.strict, **kwargs)

    def cli(self, argv: list[str], **kwargs) -> "Multi":
        data = cli_parse(argv)
        return self.dict(data, **kwargs)

    def on(self, clazz: type):
        conf, *nxts = self.confs
        for nxt in nxts:
            conf = ConfigTree.merge_configs(conf, nxt)
        return parse(conf, clazz, self.strict, **self.kwargs)


multi = Multi([])


def env(prefix: str, clazz: type, **kwargs):
    return multi.env(prefix, **kwargs).on(clazz)


def dict(obj: dict[str, Any], clazz: type, **kwargs):
    return multi.dict(obj, **kwargs).on(clazz)


def string(s: str, clazz: type, **kwargs):
    return multi.string(s, **kwargs).on(clazz)


def url(uri: str, clazz: type, **kwargs):
    return multi.url(uri, **kwargs).on(clazz)


def file(path: str, clazz: type, **kwargs):
    return multi.file(path, **kwargs).on(clazz)


def cli(argv: list[str], clazz: type, **kwargs):
    return multi.cli(argv, **kwargs).on(clazz)


def load(path: str, clazz: type, **kwargs):
    return file(path, clazz, **kwargs)


def loads(s: str, clazz: type, **kwargs):
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
        if out.lower() == "toml":
            return tomli_w.dumps(utils.__to_toml(conf))

    return conf
