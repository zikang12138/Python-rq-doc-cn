> 尽管RQ `use_connection()`为方便起见提供了该命令，但已弃用该命令，因为它会污染全局名称空间。相反，更喜欢使用`with Connection(...):`上下文管理器进行显式连接管理，或者将Redis连接引用直接传递给队列。

## Single Redis connection (easy) (单redis连接 简单)

#### 注意：

> 采用`use_connection`已经过时了。请不要`use_connection`在你的脚本中使用。而是使用显式连接管理。

在开发模式下，默认连接本地redis服务。
```python
from rq import use_connection
use_connection()

# 下面是我自己用到的方法(原文档没有)
from rq import Queue
task_queue = Queue('worker_name', connection=redis_cli)

```

在生产模式下，连接特定的redis服务
```python
from redis import Redis
from rq import use_connection

redis_cli = Redis('my.host.org', 6789, password='secret')
use_connection(redis_cli)


```
请注意会use_connection污染全局名称空间的事实。这也意味着只能使用单个连接。

## Multiple Redis connections(多个redis连接)

> 然而，单一连接模式仅在连接到单个Redis实例以及影响全局上下文（通过用use_connection()调用替换现有连接）的情况下提供便利。只有完全控制Web堆栈时，才能使用此模式。

> 在任何其他情况下，或者要使用多个连接时，都应使用Connection上下文或显式传递连接。

#### 显式连接（明确但啰嗦）
> 每个RQ对象实例（队列，工作程序，作业）都有一个connection关键字参数，可以将其传递给构造函数。使用此功能，无需使用use_connection()。相反，可以这样创建队列：

```python
from rq import Queue
from redis import Redis

conn1 = Redis('localhost', 6379)
conn2 = Redis('remote.host.org', 9836)

q1 = Queue('foo', connection=conn1)
q2 = Queue('bar', connection=conn2)
```

enqueued的每个job都会知道它属于哪个连接。worker也是如此。

这种方法非常精确，但是比较冗长，因此很啰嗦。

#### 连接上下文（精确且简洁）

> 但是，如果要使用多个连接，则有更好的方法。创建后，每个RQ对象实例将使用RQ连接堆栈上最顶层的Redis连接，这是一种临时替换要使用的默认连接的机制。

> 这个例子将有助于理解它：
```python
from rq import Queue, Connection
from redis import Redis

with Connection(Redis('localhost', 6379)):
    q1 = Queue('foo')
    with Connection(Redis('remote.host.org', 9836)):
        q2 = Queue('bar')
    q3 = Queue('qux')

assert q1.connection != q2.connection
assert q2.connection != q3.connection
assert q1.connection == q3.connection
```
> 你可以认为这似乎是在Connection上下文中，每个新创建的RQ对象实例将connection隐式设置参数。使job入q2队将其排队在第二个（远程）Redis后端中，即使在连接上下文之外。

#### 推出/弹出连接

> 例如，如果你的代码不允许你使用with语句，如果你想使用该语句来设置单元测试，则可以使用`push_connection()`和 `pop_connection()`方法而不是上下文管理器。
```python
import unittest
from rq import Queue
from rq import push_connection, pop_connection

class MyTest(unittest.TestCase):
    def setUp(self):
        push_connection(Redis())

    def tearDown(self):
        pop_connection()

    def test_foo(self):
        """Any queues created here use local Redis."""
        q = Queue()

```

## Sentinel support(容灾支持)
要使用redis Sentinel，必须在配置文件中指定字典。将此设置与具有自动重新启动选项的systemd或docker容器一起使用，可使worker和RQ与Redis具有容错连接。
```python
SENTINEL: {'INSTANCES':[('remote.host1.org', 26379), ('remote.host2.org', 26379), ('remote.host3.org', 26379)],
           'SOCKET_TIMEOUT': None,
           'PASSWORD': 'secret',
           'DB': 2,
           'MASTER_NAME': 'master'}
```
