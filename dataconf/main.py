import contextlib
import copy
import json
import os
import tomllib
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen

import pyparsing
import tomli_w
from pyhocon import ConfigFactory
from pyhocon import HOCONConverter
from pyhocon.config_parser import ConfigTree
from pyhocon.exceptions import ConfigException
from yaml import YAMLError
from yaml import safe_dump
from yaml import safe_load

from dataconf import utils
from dataconf.exceptions import MalformedConfigException
from dataconf.exceptions import ParseException

HOCON = 1
YAML = 2
TOML = 3

_LOADERS = {
    "hocon": HOCON,
    "yaml": YAML,
    "yml": YAML,
    "toml": TOML,
}


def _normalize_loader(loader):
    if isinstance(loader, str):
        return _LOADERS.get(loader.lower(), loader)
    return loader


def _stringify_keys(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        return {
            k if isinstance(k, str) else str(k): _stringify_keys(v)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_stringify_keys(v) for v in obj]
    return obj


def _hocon_parse(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except pyparsing.ParseBaseException as e:
        raise MalformedConfigException(
            f'parsing failure line {e.lineno} character {e.col}, got "{e.line}"'
        )
    except ConfigException as e:
        raise ParseException(str(e)) from e


def _yaml_load(data):
    try:
        return safe_load(data)
    except YAMLError as e:
        raise ParseException(str(e)) from e


def _toml_loads(s: str):
    try:
        return tomllib.loads(s)
    except tomllib.TOMLDecodeError as e:
        raise ParseException(str(e)) from e


def _toml_load(f):
    try:
        return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ParseException(str(e)) from e


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

    def _next(self, conf: ConfigTree, kwargs: dict) -> "Multi":
        strict = kwargs.pop("strict", self.strict)
        ignore = kwargs.pop(
            "ignore_unexpected", self.kwargs.get("ignore_unexpected", False)
        )
        return Multi(self.confs + [conf], strict, ignore_unexpected=ignore)

    def env(self, prefix: str, **kwargs) -> "Multi":
        data = env_vars_parse(prefix, os.environ)
        kwargs.setdefault("strict", False)
        return self.dict(data, **kwargs)

    def dict(self, obj: dict[str, Any], **kwargs) -> "Multi":
        if obj is None:
            obj = {}
        conf = ConfigFactory.from_dict(_stringify_keys(obj))
        return self._next(conf, kwargs)

    def string(self, s: str, loader: str = HOCON, **kwargs) -> "Multi":
        loader = _normalize_loader(loader)
        if loader == YAML:
            data = _yaml_load(s)
            return self.dict({} if data is None else data, **kwargs)

        if loader == TOML:
            data = _toml_loads(s)
            return self.dict(data, **kwargs)

        stripped = s.lstrip()
        if stripped[:1] in "{[":
            try:
                data = json.loads(s)
            except json.JSONDecodeError:
                data = None
            else:
                if isinstance(data, Mapping):
                    return self.dict(data, **kwargs)

        conf = _hocon_parse(ConfigFactory.parse_string, s)
        return self._next(conf, kwargs)

    def url(self, uri: str, timeout: int = 10, **kwargs) -> "Multi":
        parsed = urlparse(uri)
        if parsed.scheme == "file" and parsed.query:
            raise ParseException("file URLs with a query string are not supported")
        path = parsed.path.lower().rstrip("/")
        loader = _normalize_loader(kwargs.pop("loader", None))
        if loader == YAML or (loader is None and path.endswith((".yaml", ".yml"))):
            with contextlib.closing(urlopen(uri, timeout=timeout)) as fd:
                s = fd.read().decode("utf-8")
            return self.string(s, loader=YAML, **kwargs)

        if loader == TOML or (loader is None and path.endswith(".toml")):
            with contextlib.closing(urlopen(uri, timeout=timeout)) as fd:
                s = fd.read().decode("utf-8")
            return self.string(s, loader=TOML, **kwargs)

        conf = _hocon_parse(
            ConfigFactory.parse_URL, uri, timeout=timeout, required=True
        )
        return self._next(conf, kwargs)

    def file(
        self,
        path: str,
        loader: str | None = None,
        allow_missing: bool = False,
        **kwargs,
    ) -> "Multi":
        if allow_missing and not os.path.exists(path):
            return self.dict({}, **kwargs)

        loader = _normalize_loader(loader)
        lowered = path.lower()
        if loader == YAML or (loader is None and lowered.endswith((".yaml", ".yml"))):
            with open(path, "r") as f:
                data = _yaml_load(f)
            return self.dict({} if data is None else data, **kwargs)

        if loader == TOML or (loader is None and lowered.endswith(".toml")):
            with open(path, "rb") as f:
                data = _toml_load(f)
            return self.dict(data, **kwargs)

        conf = _hocon_parse(ConfigFactory.parse_file, path)
        return self._next(conf, kwargs)

    def cli(self, argv: list[str], **kwargs) -> "Multi":
        data = cli_parse(argv)
        return self.dict(data, **kwargs)

    def on(self, clazz: type):
        if not self.confs:
            conf = ConfigTree({})
        else:
            conf = copy.deepcopy(self.confs[0])
            for nxt in self.confs[1:]:
                conf = ConfigTree.merge_configs(conf, nxt)
        return parse(
            conf,
            clazz,
            self.strict,
            ignore_unexpected=self.kwargs.get("ignore_unexpected", False),
        )


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
    fmt = (out or "").lower()
    if fmt == "hocon":
        if not utils._hocon_safe_keys(conf):
            return json.dumps(utils._plain(conf), indent=2, ensure_ascii=False) + "\n"
        return HOCONConverter.to_hocon(conf)
    if fmt == "yaml":
        return safe_dump(utils._plain(conf), sort_keys=False)
    if fmt == "json":
        return json.dumps(utils._plain(conf), indent=2, ensure_ascii=False) + "\n"
    if fmt == "properties":
        return utils.__to_properties(utils._plain(conf))
    if fmt == "toml":
        return tomli_w.dumps(utils.__to_toml(conf))
    raise ParseException(
        "out format must be one of: hocon, yaml, json, properties, toml"
    )
