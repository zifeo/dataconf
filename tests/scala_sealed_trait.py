from dataclasses import dataclass
from typing import Text


class InputType:
    @dataclass(init=True, repr=True)
    class StringImpl:
        name: Text
        age: Text

        def test_method(self):
            print(f"{self.name} is {self.age} years old.")

    @dataclass(init=True, repr=True)
    class IntImpl:
        area_code: int
        phone_num: Text

        def test_method(self):
            print(f"The area code for {self.phone_num} is {str(self.area_code)}")
