from __future__ import annotations

from dataclasses import dataclass
import os
from typing import get_type_hints
from typing import Text

import dataconf
from dataconf.main import inject_callee_scope


@inject_callee_scope
def out_of_scope_assert(clazz, expected, globalns, localns):
    assert get_type_hints(clazz, globalns, localns)["a"] is expected


class TestFuturAnnotations:
    def test_43(self) -> None:
        @dataclass
        class Model:
            token: str

        os.environ["TEST_token"] = "1"
        dataconf.env("TEST_", Model)

    def test_repro(self) -> None:
        @dataclass
        class A:
            value: Text

        @dataclass
        class B:
            a: A

        out_of_scope_assert(B, A, globalns={})
