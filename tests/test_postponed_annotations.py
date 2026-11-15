from __future__ import annotations

from dataclasses import dataclass

import dataconf
from dataconf import loads
from dataconf import multi


@dataclass
class Nested:
    value: str


@dataclass
class Config:
    name: str
    count: int
    nested: Nested
    tags: list[str]
    maybe: str | None = None


@dataclass
class NestedOpt:
    c: str | None
    a: str = "a"


@dataclass
class Implicit:
    n: NestedOpt


@dataclass
class ForwardHolder:
    child: ForwardChild


@dataclass
class ForwardChild:
    x: int


class TestPostponedAnnotations:
    def test_simple(self) -> None:
        conf = """
        name = hello
        count = 1
        nested { value = x }
        tags = [a, b]
        """
        assert loads(conf, Config) == Config(
            name="hello",
            count=1,
            nested=Nested(value="x"),
            tags=["a", "b"],
            maybe=None,
        )

    def test_optional_present(self) -> None:
        conf = """
        name = hello
        count = 1
        nested { value = x }
        tags = []
        maybe = y
        """
        assert loads(conf, Config).maybe == "y"

    def test_implicit_optional_nested(self) -> None:
        assert loads("", Implicit) == Implicit(n=NestedOpt(c=None, a="a"))

    def test_forward_ref(self) -> None:
        assert loads("child { x = 1 }", ForwardHolder) == ForwardHolder(
            child=ForwardChild(x=1)
        )

    def test_cli(self) -> None:
        @dataclass
        class BasicClass:
            qwer: str

        assert multi.cli(["prog", "--qwer", "one"]).on(BasicClass) == BasicClass(
            qwer="one"
        )
        assert dataconf.dict({"qwer": "one"}, BasicClass) == BasicClass(qwer="one")
