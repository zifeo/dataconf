# Dataconf

## Getting started

```bash
pip3 install --upgrade git+https://github.com/zifeo/dataconf.git
poetry add git+https://github.com/zifeo/dataconf.git
```

## Examples

```python
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
class Config:
    test: str
    float: float
    list: List[str]
    nested: Nested
    nestedList: List[Nested]
    duration: timedelta

import dataconf
print(dataconf.load(conf, Config))

# TestConf(test='pc.home', float=2.1, list=['a', 'b'], nested=Nested(a='test'), nestedList=[Nested(a='test1')], duration=datetime.timedelta(seconds=2))
```

```python
json = dataconf.loads('confs/test.json', Config)
yaml = dataconf.loads('confs/test.yaml', Config)
hocon = dataconf.loads('confs/test.hocon', Config)
```

For full capabilities see [here](https://github.com/chimpler/pyhocon/#example-of-hocon-file).

## CI

```shell
dataconf -c confs/test.hocon -m tests.configs -d TestConf -o hocon
> dataconf.exceptions.TypeConfigException: expected type <class 'datetime.timedelta'> at .duration, got <class 'int'>
```
