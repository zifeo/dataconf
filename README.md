# Dataconf

[![Actions Status](https://github.com/zifeo/dataconf/workflows/CI/badge.svg)](https://github.com/zifeo/dataconf/actions)
[![PyPI version](https://badge.fury.io/py/dataconf.svg)](https://badge.fury.io/py/dataconf)

## Getting started

Requires at least Python 3.8.

```bash
# pypi
pip install dataconf
poetry add dataconf

# master
pip install --upgrade git+https://github.com/zifeo/dataconf.git
poetry add git+https://github.com/zifeo/dataconf.git
```

## Usage

```python
from dataclasses import dataclass, field
from typing import List, Dict, Union

conf = """
str = test
str = ${HOSTNAME}
float = 2.2
list = [
    a
    b
]
nested {
    a = test
}
nested_list = [
    {
        a = test1
    }
]
duration = 2s
union = 1
"""

@dataclass
class Nested:
    a: str

@dataclass
class Config:
    str: str
    float: float
    list: List[str]
    nested: Nested
    nested_list: List[Nested]
    duration: timedelta
    default_factory: Dict[str, str] = field(default_factory=dict)
    union: Union[str, int]

print(dataconf.load(conf, Config))
# TestConf(test='pc.home', float=2.1, list=['a', 'b'], nested=Nested(a='test'), nested_list=[Nested(a='test1')], duration=datetime.timedelta(seconds=2), default_factory={}, union=1)
```

```python
import dataconf

conf = dataconf.loads('confs/test.hocon', Config)
conf = dataconf.loads('confs/test.json', Config)
conf = dataconf.loads('confs/test.yaml', Config)
conf = dataconf.loads('confs/test.properties', Config)

dataconf.dumps('confs/test.hocon', out='hocon')
dataconf.dumps('confs/test.json', out='json')
dataconf.dumps('confs/test.yaml', out='yaml')
dataconf.dumps('confs/test.properties', out='properties')
```

Follows same api as python JSON package (e.g. `load`, `loads`, `dump`, `dumps`). 
For full HOCON capabilities see [here](https://github.com/chimpler/pyhocon/#example-of-hocon-file).

## CI

```shell
dataconf -c confs/test.hocon -m tests.configs -d TestConf -o hocon
# dataconf.exceptions.TypeConfigException: expected type <class 'datetime.timedelta'> at .duration, got <class 'int'>
```
