from dataclasses import dataclass
from datetime import datetime
from datetime import timezone

from pytest_httpserver import HTTPServer

import dataconf
from dataconf import dumps
from dataconf import load
from dataconf import loads
from dataconf.main import file
from dataconf.main import url
from tests.conftest import file_handler


@dataclass
class Nested:
    c: str


@dataclass
class Simple:
    hello: str
    foo: list[str]


class TestToml:
    def test_string(self) -> None:
        conf = """
        b = { c = "test" }
        """

        @dataclass
        class A:
            b: Nested

        assert loads(conf, A, loader=dataconf.TOML) == A(b=Nested(c="test"))

    def test_file(self) -> None:
        expected = Simple(hello="bonjour", foo=["bar"])
        assert file("confs/simple.toml", Simple) == expected
        assert load("confs/simple.toml", Simple) == expected
        assert load("confs/simple.toml", Simple, loader=dataconf.TOML) == expected

    def test_url(self, httpserver: HTTPServer) -> None:
        httpserver.expect_request("/simple.toml").respond_with_handler(
            file_handler("confs/simple.toml")
        )

        assert url(httpserver.url_for("/simple.toml"), Simple) == Simple(
            hello="bonjour", foo=["bar"]
        )

    def test_datetime(self) -> None:
        @dataclass
        class A:
            when: datetime

        naive = loads("when = 2000-01-01T20:00:00", A, loader=dataconf.TOML)
        assert naive == A(when=datetime(2000, 1, 1, 20, 0, 0))

        aware = loads("when = 2000-01-01T20:00:00Z", A, loader=dataconf.TOML)
        assert aware == A(when=datetime(2000, 1, 1, 20, 0, 0, tzinfo=timezone.utc))

        date_only = loads("when = 2000-01-01", A, loader=dataconf.TOML)
        assert date_only == A(when=datetime(2000, 1, 1))

    def test_optional_omitted(self) -> None:
        @dataclass
        class A:
            hello: str
            maybe: str | None = None

        assert loads('hello = "x"', A, loader=dataconf.TOML) == A(hello="x", maybe=None)

    def test_dump_roundtrip(self, tmp_path) -> None:
        original = Simple(hello="bonjour", foo=["bar"])
        path = tmp_path / "simple.toml"
        dataconf.dump(str(path), original, out="toml")
        assert load(str(path), Simple) == original

        text = dumps(original, out="toml")
        assert loads(text, Simple, loader=dataconf.TOML) == original

    def test_dump_skips_none(self) -> None:
        @dataclass
        class A:
            hello: str
            maybe: str | None = None

        text = dumps(A(hello="x"), out="toml")
        assert "maybe" not in text
        assert loads(text, A, loader=dataconf.TOML) == A(hello="x", maybe=None)
