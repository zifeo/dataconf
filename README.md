# Dataconf

## Getting started

```bash
pip3 install --upgrade git+https://github.com/zifeo/dataconf.git
poetry add git+https://github.com/zifeo/dataconf.git
```

## Examples

```python
conf = """
float = 2.2
list = [
    a
    b
]
nested {
    a = test
}
nestedList = [
    {
        a = test1
    }
]
duration = 2s
"""

@dataclass
class Nested:
    a: str

@dataclass
class Conf:
    float: float
    list: List[str]
    nested: Nested
    nestedList: List[Nested]
    duration: timedelta

import dataclass
print(dataclass.load(conf, Conf))

# TestConf(str='test', list=['a', 'b'], nested=Nested(a='test'), nestedList=[Nested(a='test1')], duration=datetime.timedelta(seconds=2))
```
