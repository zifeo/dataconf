import os
import subprocess
import sys
from dataclasses import InitVar
from dataclasses import dataclass
from dataclasses import field
from datetime import date
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from enum import Enum
from pathlib import Path
from typing import Literal
from typing import NewType
from uuid import UUID

import pytest
from dateutil.relativedelta import relativedelta
from pytest_httpserver import HTTPServer

import dataconf
from dataconf import dumps
from dataconf import loads
from dataconf.exceptions import MalformedConfigException
from dataconf.exceptions import ParseException
from dataconf.exceptions import TypeConfigException
from dataconf.utils import __env_vars_parse as env_parse
from tests.conftest import file_handler

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
            when=datetime(2000, 1, 1, 20, tzinfo=timezone.utc),
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
