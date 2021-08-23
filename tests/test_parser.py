from dataclasses import dataclass
from dataclasses import field
from typing import Dict, List, Optional, Text, Union

from dataconf import loads
from dataconf.exceptions import MissingTypeException
from dataconf.exceptions import UnexpectedKeysException
from dateutil.relativedelta import relativedelta
import pytest


class TestParser:
    def test_simple(self):
        @dataclass
        class A:
            a: Text

        conf = """
        a = test
        """
        assert loads(conf, A) == A(a="test")

    def test_relativedelta(self):
        @dataclass
        class A:
            a: relativedelta

        conf = """
        a = 2d
        """
        assert loads(conf, A) == A(a=relativedelta(days=2))

    def test_list(self):
        @dataclass
        class A:
            a: List[Text]

        conf = """
        a = [
            test
        ]
        """
        assert loads(conf, A) == A(a=["test"])

    def test_boolean(self):
        @dataclass
        class A:
            a: bool

        conf = """
        a = false
        """
        assert loads(conf, A) == A(a=False)

    def test_dict(self):
        @dataclass
        class A:
            a: Dict[Text, Text]

        conf = """
        a {
            b = test
        }
        """
        assert loads(conf, A) == A(a={"b": "test"})

    def test_nested(self):
        @dataclass
        class B:
            a: Text

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
            a: Text

        @dataclass
        class A:
            b: Union[B, Text]

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
            b: Optional[Text] = None

        conf = ""
        assert loads(conf, A) == A(b=None)

        conf = """
        b = test
        """
        assert loads(conf, A) == A(b="test")

    def test_optional_with_default(self):
        @dataclass
        class A:
            b: Optional[Text]

        conf = ""
        assert loads(conf, A) == A(b=None)

        conf = """
        b = test
        """
        assert loads(conf, A) == A(b="test")

    def test_empty_list(self):
        @dataclass
        class A:
            b: List[Text] = field(default_factory=list)

        conf = ""
        assert loads(conf, A) == A(b=[])

    def test_json(self):
        @dataclass
        class A:
            b: Text

        conf = """
        {
            "b": "c"
        }
        """
        assert loads(conf, A) == A(b="c")

    def test_yaml(self):
        @dataclass
        class A:
            b: Text

        conf = """
        b: c
        """
        assert loads(conf, A) == A(b="c")

    def test_default_value(self):
        @dataclass
        class A:
            b: Text = "c"

        assert loads("", A) == A(b="c")

    def test_root_dict(self):

        conf = """
        b: c
        """
        assert loads(conf, Dict[Text, Text]) == dict(b="c")

    def test_missing_type(self):

        with pytest.raises(MissingTypeException):
            loads("", Dict)

        with pytest.raises(MissingTypeException):
            loads("", List)

    def test_misformat(self):

        conf = """
        b {}
        c {
            f {
        }
        d {}
        }
        """

        @dataclass
        class Clazz:
            f: Dict[Text, Text] = field(default_factory=dict)

        with pytest.raises(UnexpectedKeysException):
            loads(conf, Dict[Text, Clazz])
