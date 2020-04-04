1.2.0版本的新功能

此内置版本`RQScheduler`仍然为Alpha(测试版本),使用风险自担。

如果你需要使用battle tested(经过测试)的版本，可以改用https://github.com/rq/rq-scheduler代替。

RQ 1.2.0版本的新增了`RQScheduler`，这是一个内置组建，可以安排调度任务将来执行。

这个组件是根据开发外部`rq-scheduler`库的经验开发的 。内部使用此组件的目的是使RQ具有作业调度功能，而无需：

- 1，运行单独的`rqscheduler`CLI命令。
- 2，担心一个单独的`Scheduler`类。

## Scheduling Jobs for Execution(执行调度任务)

> 有两个主要的 API 去执行调度任务，`enqueue_at()` 和 `enqueue_in()`.

> `queue.enqueue_at()`使用很像`queue.enqueue()`,除了它的第一个参数需要时间戳外。

```python
from datetime import datetime
from rq import Queue
from redis import Redis
from somewhere import say_hello

queue = Queue(name='default', connection=Redis())

# 调度任务会在当地时区的2019年10月10号9点15分运行
job = queue.enqueue_at(datetime(2019, 10, 8, 9, 15), say_hello)
```

提示：如果传入了原始的时间对象,RQ会自动将其转换为本地时区。

> `queue.enqueue_in()`接受 `timedelta`作为其第一个参数。
```python
from datetime import timedelta
from rq import Queue
from redis import Redis
from somewhere import say_hello

queue = Queue(name='default', connection=Redis())

# 调度任务会在10秒后运行
job = queue.enqueue_at(timedelta(seconds=10), say_hello)
```

> 计划执行的任务不会放入队列中，而是存储在`ScheduledJobRegistry`中。

```python

from datetime import timedelta
from redis import Redis

from rq import Queue
from rq.registry import ScheduledJobRegistry

redis = Redis()

queue = Queue(name='default', connection=redis)
job = queue.enqueue_in(timedelta(seconds=10), say_nothing)
print(job in queue)  # 输出False因为job不在enqueue中

registry = ScheduledJobRegistry(queue=queue)
print(job in registry)  # 输出True因为job在ScheduledJobRegistry中

```

## Running the Scheduler(运行调度功能)

> 如果使用RQ的调度功能，则需要在启用调度程序组件的情况下运行RQ工作程序。
```python
$ rq worker --with-scheduler
```
> 还可以以编程方式运行启用了调度程序的工作程序。

```python

from rq import Worker, Queue
from redis import Redis

redis = Redis()

queue = Queue(connection=redis)
worker = Worker(queues=[queue], connection=redis)
worker.work(with_scheduler=True)

```
任何时候只有一个调度程序可以针对特定队列运行。如果在启用了调度程序的情况下运行多个工作程序，则只有一个调度程序将为给定队列积极工作。

活动调度程序负责使调度的job入队列。活动的计划程序将每秒检查一次计划的Job。

空闲的调度程序将定期（每15分钟）检查他们负责的队列是否有活动的调度程序。如果没有，则其中一个空闲的调度程序将开始工作。这样，如果具有活动调度程序的worker死亡，则在启用了调度组件的情况下，其他worker将接手调度工作。
