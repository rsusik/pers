# Persistent results

<p align="center">
<a href="https://pypi.org/project/pers" target="_blank">
    <img src="https://img.shields.io/pypi/v/pers?color=%2334D058&label=pypi%20package" alt="Package version">
</a>
<a href="https://github.com/rsusik/pers/blob/master/LICENSE" target="_blank">
    <img src="https://img.shields.io/github/license/rsusik/pers" alt="Package version">
</a>
</p>

Persistent results is a Python class that ensures the results of tests will be available even if interruptions during the tests occur.

## Installation:

```
pip install pers
```

## Usage:

### Example 1

If the code below breaks for some reason (let's say the computer shuts down because of a power outage or some exception), you can restart it to continue from the step it finished.

```python
from pers import PersistentResults
import pandas as pd

results = PersistentResults(
    'test.pickle', # filename for result caching
    interval=1,    # how often dump the results
    tmpfilename='~test.pickle' # tmp cache file (optional)
)

fun = lambda x, y, a, b: x**2 + y
for x in range(10):
    for y in range(11):
        results.append(fun, x, y, a=x, b=y)
results.save()

print(results[90])
print(len(results))
print(pd.DataFrame(results.data))
```

Output:

```
{'result': 66, 'x': 8, 'y': 2, 'a': 8, 'b': 2}
110
|     |   result |   x |   y |   a |   b |
|----:|---------:|----:|----:|----:|----:|
|   0 |        0 |   0 |   0 |   0 |   0 |
|   1 |        1 |   0 |   1 |   0 |   1 |
|   2 |        2 |   0 |   2 |   0 |   2 |
[..]
| 107 |       89 |   9 |   8 |   9 |   8 |
| 108 |       90 |   9 |   9 |   9 |   9 |
| 109 |       91 |   9 |  10 |   9 |  10 |
```







### Example 2


```python
from pers import PersistentResults
import pandas as pd

results = PersistentResults(
    'test2.pickle',
    interval=1,
    result_prefix='' # we do not want a prefix _result_
)

def fun(x, y, a, b):
    print(f'x: {x}, y:{y}')
    return {         # yes, we can return dictionary
        'out': x**2 + y,
        'x': x,      # yes, we can return input in dict
        'a': a,
    }

try:
    for x in range(10):
        for y in range(11):
            results.append(fun, x=x, y=y, a=x, b=y)
            if x == 5 and y ==5: # simulate reboot
                raise Exception('Unexpected reboot...')
except:
    pass

# RERUN the tests
# will skip already processed elements

for x in range(10):
    for y in range(11):
        results.append(fun, x=x, y=y, a=x, b=y)
results.save()

print(pd.DataFrame(results.data).to_markdown())
```


```
x: 0, y:0
x: 0, y:1
[..]
x: 5, y:4
x: 5, y:5
Unexpected reboot...

x: 5, y:6
x: 5, y:7
[..]
x: 9, y:9
x: 9, y:10

|     |   out |   x |   a |   y |   b |
|----:|------:|----:|----:|----:|----:|
|   0 |     0 |   0 |   0 |   0 |   0 |
|   1 |     1 |   0 |   0 |   1 |   1 |
|   2 |     2 |   0 |   0 |   2 |   2 |
[..]
| 107 |    89 |   9 |   9 |   8 |   8 |
| 108 |    90 |   9 |   9 |   9 |   9 |
| 109 |    91 |   9 |   9 |  10 |  10 |
```