from dataclasses import dataclass
from typing import Text


class InputType:
    @dataclass(init=True, repr=True)
    class StringImpl:
        name: Text
        age: Text

        def test_method(self):
            return f"{self.name} is {self.age} years old."

        def test_complex(self):
            return int(self.age) * 3

    @dataclass(init=True, repr=True)
    class IntImpl:
        area_code: int
        phone_num: Text

        def test_method(self):
            return f"The area code for {self.phone_num} is {str(self.area_code)}"

        def test_complex(self):
            return self.area_code - 10
