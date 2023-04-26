import contextlib
import os
from typing import Any, Optional
from typing import Dict
from typing import List
from typing import Type
from urllib.parse import urlparse
from urllib.request import urlopen

from dataconf import utils
from dataconf.exceptions import MalformedConfigException
from pyhocon import ConfigFactory
from pyhocon import HOCONConverter
from pyhocon.config_parser import ConfigTree
import pyparsing
from yaml import safe_load

HOCON = 1
YAML = 2


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
    def __init__(self, confs: List[ConfigTree], strict: bool = True, **kwargs) -> None:
        self.confs = confs
        self.strict = strict
        self.kwargs = kwargs

    def env(self, prefix: str, **kwargs) -> "Multi":
        self.strict = False
        data = env_vars_parse(prefix, os.environ)
        return self.dict(data, **kwargs)

    def dict(self, obj: Dict[str, Any], **kwargs) -> "Multi":
        conf = ConfigFactory.from_dict(obj)
        return Multi(self.confs + [conf], self.strict, **kwargs)

    def string(self, s: str, loader: str = HOCON, **kwargs) -> "Multi":
        if loader == YAML:
            data = safe_load(s)
            return self.dict(data, **kwargs)

        conf = ConfigFactory.parse_string(s)
        return Multi(self.confs + [conf], self.strict, **kwargs)

    def url(self, uri: str, timeout: int = 10, **kwargs) -> "Multi":
        path = urlparse(uri).path
        if path.endswith(".yaml") or path.endswith(".yml"):
            with contextlib.closing(urlopen(uri, timeout=timeout)) as fd:
                s = fd.read().decode("utf-8")
            return self.string(s, loader=YAML, **kwargs)

        conf = ConfigFactory.parse_URL(uri, timeout=timeout, required=True)
        return Multi(self.confs + [conf], self.strict, **kwargs)

    def file(self, path: str, loader: Optional[str] = None, **kwargs) -> "Multi":
        if loader == YAML or (
            loader is None and (path.endswith(".yaml") or path.endswith(".yml"))
        ):
            with open(path, "r") as f:
                data = safe_load(f)
            return self.dict(data, **kwargs)

        conf = ConfigFactory.parse_file(path)
        return Multi(self.confs + [conf], self.strict, **kwargs)

    def cli(self, argv: List[str], **kwargs) -> "Multi":
        data = cli_parse(argv)
        return self.dict(data, **kwargs)

    def on(self, clazz: Type):
        conf, *nxts = self.confs
        for nxt in nxts:
            conf = ConfigTree.merge_configs(conf, nxt)
        return parse(conf, clazz, self.strict, **self.kwargs)


multi = Multi([])


def env(prefix: str, clazz: Type, **kwargs):
    return multi.env(prefix, **kwargs).on(clazz)


def dict(obj: Dict[str, Any], clazz: Type, **kwargs):
    return multi.dict(obj, **kwargs).on(clazz)


def string(s: str, clazz: Type, **kwargs):
    return multi.string(s, **kwargs).on(clazz)


def url(uri: str, clazz: Type, **kwargs):
    return multi.url(uri, **kwargs).on(clazz)


def file(path: str, clazz: Type, **kwargs):
    return multi.file(path, **kwargs).on(clazz)


def cli(argv: List[str], clazz: Type, **kwargs):
    return multi.cli(argv, **kwargs).on(clazz)


def load(path: str, clazz: Type, **kwargs):
    return file(path, clazz, **kwargs)


def loads(s: str, clazz: Type, **kwargs):
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
