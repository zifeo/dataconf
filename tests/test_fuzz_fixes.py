import json
import os
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import InitVar
from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from enum import Enum
from pathlib import Path
from typing import Final
from typing import Literal
from typing import NewType
from uuid import UUID

import pytest
from dateutil.relativedelta import relativedelta
from pyhocon import ConfigFactory
from pytest_httpserver import HTTPServer

import dataconf
from dataconf import dumps
from dataconf import loads
from dataconf.exceptions import MalformedConfigException
from dataconf.exceptions import ParseException
from dataconf.exceptions import TypeConfigException
from dataconf.exceptions import UnexpectedKeysException
from dataconf.main import parse
from dataconf.utils import __cli_parse as cli_parse
from dataconf.utils import __env_vars_parse as env_parse
from tests.conftest import file_handler
from tests.test_parse import InputType
from tests.test_parse import StringImpl

UserId = NewType("UserId", int)


class Color(Enum):
    RED = "red"
    GREEN = 2


@dataclass
class Simple:
    hello: str
    foo: list[str]


class TestFuzzFixes:
    def test_optional_does_not_swallow(self) -> None:
        @dataclass
        class A:
            x: str | None

        with pytest.raises(TypeConfigException):
            dataconf.dict({"x": 1.5}, A)

    def test_list_none_union(self) -> None:
        @dataclass
        class A:
            xs: list[str] | None = None

        assert dataconf.dict({}, A) == A(xs=None)
        assert dataconf.dict({"xs": None}, A) == A(xs=None)
        assert loads("xs = null", A) == A(xs=None)

    def test_str_not_a_list(self) -> None:
        @dataclass
        class A:
            x: list[str]

        with pytest.raises(TypeConfigException):
            dataconf.dict({"x": "ab"}, A)

    def test_empty_fixed_tuple(self) -> None:
        @dataclass
        class A:
            x: tuple[int, str]

        with pytest.raises(MalformedConfigException):
            dataconf.dict({"x": []}, A)

    def test_dict_none_required(self) -> None:
        @dataclass
        class A:
            x: dict[str, int]

        with pytest.raises(MalformedConfigException):
            dataconf.dict({"x": None}, A)

    def test_empty_yaml_defaults(self) -> None:
        @dataclass
        class A:
            a: str = "x"

        assert loads("", A, loader=dataconf.YAML) == A()
        assert loads("", A, loader="yaml") == A()

    def test_strict_false_hocon(self) -> None:
        @dataclass
        class A:
            n: int

        assert loads('n = "1"', A, strict=False) == A(n=1)

    def test_date_field(self) -> None:
        @dataclass
        class A:
            d: date

        assert dataconf.dict({"d": "2000-01-01"}, A) == A(d=date(2000, 1, 1))
        assert loads("d = 2000-01-01", A, loader=dataconf.TOML) == A(d=date(2000, 1, 1))

    def test_timedelta_native(self) -> None:
        @dataclass
        class A:
            d: timedelta

        assert dataconf.dict({"d": timedelta(milliseconds=2)}, A) == A(
            d=timedelta(milliseconds=2)
        )
        assert loads("d = 2s", A) == A(d=timedelta(seconds=2))

    def test_enum_name_and_value(self) -> None:
        @dataclass
        class A:
            c: Color

        assert dataconf.dict({"c": "RED"}, A) == A(c=Color.RED)
        assert dataconf.dict({"c": "red"}, A) == A(c=Color.RED)
        assert dataconf.dict({"c": 2}, A) == A(c=Color.GREEN)

    def test_properties_list_indexes(self) -> None:
        text = "hello = bonjour\nfoo.0 = bar\n"
        assert loads(text, Simple) == Simple(hello="bonjour", foo=["bar"])

    def test_env_nested_list_no_spare(self) -> None:
        assert env_parse("P", {"P_LSLS_0_0": "f", "P_LSLS_0_1": "g"}) == {
            "lsls": [["f", "g"]]
        }

    def test_env_list_10(self) -> None:
        data = env_parse("P", {f"P_LS_{i}": str(i) for i in range(11)})
        assert data == {"ls": [str(i) for i in range(11)]}

    def test_env_compose_without_parent(self) -> None:
        assert env_parse("P", {"P_A_80": "2"}) == {"a_80": "2"}

    def test_env_nest_under_scalar(self) -> None:
        with pytest.raises(ParseException):
            env_parse("P", {"P_A": "1", "P_A__B": "2"})

    def test_implicit_optional_keeps_default(self) -> None:
        @dataclass
        class Nested:
            c: str | None = "hello"
            a: str = "a"

        @dataclass
        class Outer:
            n: Nested

        assert loads("", Outer) == Outer(n=Nested())

    def test_init_false(self) -> None:
        @dataclass
        class A:
            a: str
            b: int = field(init=False, default=9)

        assert dataconf.dict({"a": "x"}, A) == A(a="x")

    def test_initvar_default(self) -> None:
        @dataclass
        class A:
            a: str
            x: InitVar[int] = 0

            def __post_init__(self, x: int):
                self.x = x

        got = dataconf.dict({"a": "x"}, A)
        assert got.a == "x"

    def test_union_dataclasses(self) -> None:
        @dataclass
        class A:
            x: int

        @dataclass
        class B:
            y: str

        @dataclass
        class C:
            v: A | B

        assert dataconf.dict({"v": {"y": "hello"}}, C) == C(v=B(y="hello"))

    def test_newtype_uuid_bytes(self) -> None:
        @dataclass
        class A:
            u: UserId
            id: UUID
            raw: bytes

        got = dataconf.dict(
            {"u": 7, "id": "12345678-1234-5678-1234-567812345678", "raw": "hi"},
            A,
        )
        assert got.u == 7
        assert got.id.int
        assert got.raw == b"hi"

    def test_dump_tuple_json_yaml(self) -> None:
        @dataclass
        class A:
            v: tuple[str, int]
            p: Path
            when: datetime
            d: timedelta

        original = A(
            v=("a", 1),
            p=Path("/tmp/x"),
            when=datetime(2000, 1, 1, 20, tzinfo=UTC),
            d=timedelta(days=1, hours=2),
        )
        for fmt in ("hocon", "yaml", "json", "toml"):
            text = dumps(original, out=fmt)
            loader = {
                "hocon": dataconf.HOCON,
                "yaml": dataconf.YAML,
                "json": dataconf.HOCON,
                "toml": dataconf.TOML,
            }[fmt]
            assert loads(text, A, loader=loader) == original

    def test_yaml_keeps_list_null(self) -> None:
        @dataclass
        class A:
            xs: list[str | None]

        text = dumps(A(xs=["a", None, "b"]), out="yaml")
        assert loads(text, A, loader=dataconf.YAML) == A(xs=["a", None, "b"])

    def test_unknown_dump_format(self) -> None:
        @dataclass
        class A:
            a: str

        with pytest.raises(ParseException):
            dumps(A(a="x"), out="xml")

    def test_empty_multi(self) -> None:
        @dataclass
        class A:
            a: str = "x"

        assert dataconf.multi.on(A) == A()

    def test_ignore_unexpected_persists(self) -> None:
        @dataclass
        class A:
            a: str

        assert dataconf.multi.string(
            "a = hello\nb = extra", ignore_unexpected=True
        ).string("a = later").on(A) == A(a="later")

    def test_multi_does_not_mutate(self) -> None:
        @dataclass
        class A:
            n: int

        base = dataconf.multi.string("n = 1")
        assert base.dict({"n": 2}).on(A) == A(n=2)
        assert base.on(A) == A(n=1)

    def test_relativedelta_hocon_dump(self) -> None:
        @dataclass
        class A:
            a: relativedelta

        original = A(a=relativedelta(years=1, months=2, days=3, hours=4))
        text = dumps(original, out="hocon")
        assert loads(text, A) == original

    def test_empty_tuple_type(self) -> None:
        @dataclass
        class A:
            x: tuple[()]

        assert dataconf.dict({"x": []}, A) == A(x=())
        with pytest.raises(MalformedConfigException):
            dataconf.dict({"x": [1]}, A)

    def test_literal_rejects_bool_for_int(self) -> None:
        @dataclass
        class A:
            x: Literal[1]

        with pytest.raises(TypeConfigException):
            dataconf.dict({"x": True}, A)

    def test_union_list_or_str(self) -> None:
        @dataclass
        class A:
            x: list[str] | str

        assert dataconf.dict({"x": "ab"}, A) == A(x="ab")
        assert dataconf.dict({"x": ["a", "b"]}, A) == A(x=["a", "b"])

    def test_yaml_suffix_case(self, tmp_path: Path) -> None:
        dest = tmp_path / "simple.YAML"
        dest.write_text(Path("confs/simple.yaml").read_text())
        assert dataconf.file(str(dest), Simple) == Simple(hello="bonjour", foo=["bar"])

    def test_url_loader_override(self, httpserver: HTTPServer) -> None:
        httpserver.expect_request("/simple.hocon").respond_with_handler(
            file_handler("confs/simple.yaml")
        )
        assert dataconf.url(
            httpserver.url_for("/simple.hocon"), Simple, loader=dataconf.YAML
        ) == Simple(hello="bonjour", foo=["bar"])

    def test_python_module_entrypoint(self) -> None:
        env = {
            **os.environ,
            "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
        }
        help_result = subprocess.run(
            [sys.executable, "-m", "dataconf", "-h"],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        assert help_result.returncode == 0
        assert "--out" in help_result.stdout

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "dataconf",
                "-c",
                "confs/simple.yaml",
                "-m",
                "tests.test_fuzz_fixes",
                "-d",
                "Simple",
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        assert result.returncode == 0
        assert "bonjour" in result.stdout

    def test_mapping_annotation(self) -> None:
        @dataclass
        class A:
            m: Mapping[str, int]

        assert dataconf.dict({"m": {"a": 1}}, A) == A(m={"a": 1})

    def test_default_factory_dataclass_list(self) -> None:
        @dataclass
        class Nested:
            a: int = 1

        @dataclass
        class A:
            xs: list[Nested] = field(default_factory=lambda: [Nested()])

        assert dataconf.dict({}, A) == A(xs=[Nested()])

    def test_type_does_not_mutate_config(self) -> None:
        conf = ConfigFactory.from_dict(
            {"_type": "StringImpl", "name": "ada", "age": "1"}
        )
        got = parse(conf, InputType)
        assert got == StringImpl(name="ada", age="1")
        assert conf["_type"] == "StringImpl"

    def test_time_value(self) -> None:
        @dataclass
        class A:
            t: time

        assert dataconf.dict({"t": time(1, 2, 3)}, A) == A(t=time(1, 2, 3))
        assert loads('t = "01:02:03"', A) == A(t=time(1, 2, 3))

    def test_ignore_unexpected_does_not_flip_union(self) -> None:
        @dataclass
        class A:
            x: int

        @dataclass
        class B:
            x: int
            y: str

        @dataclass
        class C:
            v: A | B

        assert dataconf.dict({"v": {"x": 1, "y": "z"}}, C, ignore_unexpected=True) == C(
            v=B(x=1, y="z")
        )

    def test_bool_str_union_keeps_string(self) -> None:
        @dataclass
        class A:
            v: bool | str

        assert dataconf.dict({"v": "true"}, A) == A(v="true")
        assert dataconf.dict({"v": True}, A) == A(v=True)

    def test_empty_mapping_is_not_a_list(self) -> None:
        @dataclass
        class A:
            xs: list[str]

        with pytest.raises(TypeConfigException):
            dataconf.dict({"xs": {}}, A)

    def test_final_int(self) -> None:
        @dataclass
        class A:
            x: Final[int]

        assert dataconf.dict({"x": 3}, A) == A(x=3)

    @pytest.mark.skipif(sys.version_info < (3, 12), reason="PEP 695")
    def test_pep695_alias(self) -> None:
        from typing import TypeAliasType

        AliasId = TypeAliasType("AliasId", int)

        @dataclass
        class A:
            u: AliasId

        assert dataconf.dict({"u": 7}, A).u == 7

    def test_env_scalar_then_index(self) -> None:
        with pytest.raises(ParseException):
            env_parse("P", {"P_A": "hello", "P_A_0": "world"})

    def test_empty_env_and_cli_key(self) -> None:
        with pytest.raises(ParseException, match="empty"):
            env_parse("EMP", {"EMP_": "{}"})
        with pytest.raises(ParseException, match="empty"):
            cli_parse(["--", "x"])

    def test_env_int_dict_keys_are_strings(self) -> None:
        assert env_parse("P", {"P_0": "1"}) == {"0": "1"}

    def test_env_leading_zeros_and_unicode_digits(self) -> None:
        assert env_parse("P", {"P_A_01": "x"}) == {"a_01": "x"}
        assert env_parse("P", {"P_A_\u0661": "x"}) == {"a_\u0661": "x"}

    def test_env_missing_substitution_is_parse_exception(self) -> None:
        with pytest.raises(ParseException):
            env_parse("P", {"P_NESTED_": "${MISSING_DATACONF_VAR}"})

    def test_yaml_non_str_keys(self) -> None:
        @dataclass
        class A:
            m: dict[str, int]

        assert loads("m:\n  1: 2\n", A, loader=dataconf.YAML) == A(m={"1": 2})
        assert loads("m:\n  true: 2\n", A, loader=dataconf.YAML) == A(m={"True": 2})

    def test_json_unicode_escape(self) -> None:
        @dataclass
        class A:
            s: str

        assert loads('{"s": "\\u00e9"}', A) == A(s="é")

    def test_yaml_and_toml_errors_are_parse_exception(self) -> None:
        @dataclass
        class A:
            s: str

        with pytest.raises(ParseException):
            loads(":\n:", A, loader=dataconf.YAML)
        with pytest.raises(ParseException):
            loads("s = [", A, loader=dataconf.TOML)

    def test_url_trailing_slash_yaml(self, httpserver: HTTPServer) -> None:
        @dataclass
        class A:
            hello: str
            foo: list[str]

        httpserver.expect_request("/simple.yaml/").respond_with_handler(
            file_handler("confs/simple.yaml")
        )
        got = dataconf.url(httpserver.url_for("/simple.yaml/"), A)
        assert got == A(hello="bonjour", foo=["bar"])

    def test_file_url_query_rejected(self) -> None:
        @dataclass
        class A:
            hello: str

        with pytest.raises(ParseException, match="query"):
            dataconf.url("file:///tmp/missing.yaml?x=1", A)

    def test_bytes_dump_roundtrip(self) -> None:
        @dataclass
        class A:
            raw: bytes

        original = A(raw=b"hi")
        text = dumps(original, out="json")
        assert loads(text, A) == original

    def test_dotted_dict_keys_dump(self) -> None:
        @dataclass
        class A:
            m: dict[str, int]

        original = A(m={"a.b": 1})
        text = dumps(original, out="json")
        assert json.loads(text) == {"m": {"a.b": 1}}
        hocon = dumps(original, out="hocon")
        assert "a.b" in hocon
        dumps(original, out="yaml")
        with pytest.raises(ParseException, match="cannot encode dict keys"):
            dumps(original, out="properties")

    def test_init_false_not_dumped(self) -> None:
        @dataclass
        class A:
            a: str
            b: int = field(init=False, default=9)

        text = dumps(A(a="x"), out="hocon")
        assert "b" not in text
        assert loads(text, A) == A(a="x")

    def test_toml_none_dict_value_raises(self) -> None:
        @dataclass
        class A:
            m: dict[str, str | None]

        with pytest.raises(ParseException, match="null dict values"):
            dumps(A(m={"a": None}), out="toml")

    def test_properties_quotes_and_empty_list(self) -> None:
        @dataclass
        class A:
            p: Path
            xs: list[str]
            s: str

        text = dumps(
            A(p=Path("/tmp/\tx"), xs=[], s="a=b"),
            out="properties",
        )
        assert 's = "a=b"' in text
        assert "xs = []" in text
        with pytest.raises(ParseException, match="null list items"):
            dumps(A(p=Path("x"), xs=["a", None], s="s"), out="properties")  # type: ignore[list-item]

    def test_parse_does_not_leave_type_error_from_subclasses(self) -> None:
        @dataclass
        class A:
            extra: str

        with pytest.raises(UnexpectedKeysException):
            dataconf.dict({"extra": "x", "nope": 1}, A)
