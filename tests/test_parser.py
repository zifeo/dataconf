from dataclasses import dataclass
from dataclasses import field
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from dataconf import loads


class TestParser:
    def test_simple(self):
        @dataclass
        class A:
            a: str

        conf = """
        a = test
        """
        assert loads(conf, A) == A(a="test")

    def test_list(self):
        @dataclass
        class A:
            a: List[str]

        conf = """
        a = [
            test
        ]
        """
        assert loads(conf, A) == A(a=["test"])

    def test_dict(self):
        @dataclass
        class A:
            a: Dict[str, str]

        conf = """
        a {
            b = test
        }
        """
        assert loads(conf, A) == A(a={"b": "test"})

    def test_nested(self):
        @dataclass
        class B:
            a: str

        @dataclass
        class A:
            b: B

        conf = """
        b {
            a = test
        }
        """
        assert loads(conf, A) == A(b=B(a="test"))

    def test_union(self):
        @dataclass
        class B:
            a: str

        @dataclass
        class A:
            b: Union[B, str]

        conf = """
        b {
            a = test
        }
        """
        assert loads(conf, A) == A(b=B(a="test"))

        conf = """
        b = test
        """
        assert loads(conf, A) == A(b="test")

    def test_optional(self):
        @dataclass
        class A:
            b: Optional[str] = None

        conf = ""
        assert loads(conf, A) == A(b=None)

        conf = """
        b = test
        """
        assert loads(conf, A) == A(b="test")

    def test_optional_with_default(self):
        @dataclass
        class A:
            b: Optional[str]

        conf = ""
        assert loads(conf, A) == A(b=None)

        conf = """
        b = test
        """
        assert loads(conf, A) == A(b="test")

    def test_empty_list(self):
        @dataclass
        class A:
            b: List[str] = field(default=lambda: [])

        conf = ""
        assert loads(conf, A) == A(b=[])

    def test_json(self):
        @dataclass
        class A:
            b: str

        conf = """
        {
            "b": "c"
        }
        """
        assert loads(conf, A) == A(b="c")

    def test_yaml(self):
        @dataclass
        class A:
            b: str

        conf = """
        b: c
        """
        assert loads(conf, A) == A(b="c")
