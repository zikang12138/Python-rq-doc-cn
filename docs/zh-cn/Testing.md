## Workers inside unit tests(单元测试中的worker)

> 你可能希望将RQ任务包含在单元测试中。但是，许多框架（例如Django）使用的内存数据库fork()在RQ 的默认行为上不能很好地发挥作用。

> 因此，必须使用SimpleWorker类来避免fork（）;。
```python
from redis import Redis
from rq import SimpleWorker, Queue

queue = Queue(connection=Redis())
queue.enqueue(my_long_running_job)
worker = SimpleWorker([queue], connection=queue.connection)
worker.work(burst=True)  # Runs enqueued job
# Check for result...
```

## Running Jobs in unit tests(在单元测试中运行job)

> 用于测试目的的另一种解决方案是使用`is_async=Falsequeue`参数，该参数指示它立即在同一线程中执行job，而不是将其分派给worker。不再需要worker。此外，我们可以使用伪造的Redis来模拟Redis实例，因此我们不必单独运行Redis服务器。伪redis服务器的实例可以作为连接参数直接传递到队列：

```python
from fakeredis import FakeStrictRedis
from rq import Queue

queue = Queue(is_async=False, connection=FakeStrictRedis())
job = queue.enqueue(my_long_running_job)
assert job.is_finished
```