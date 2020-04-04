每个队列都维护一组任务注册表。

- StartedJobRegistry保留当前正在执行的job，job在执行前即被添加，在完成（成功或失败）后即被删除。
- FinishedJobRegistry 保留成功完成的job。
- FailedJobRegistry 保留已执行但未成功完成的job。
- DeferredJobRegistry 保留延迟的job（依赖于另一个job并正在等待该job完成的job）。
- ScheduledJobRegistry 保留计划的job。

You can get the number of jobs in a registry, the ids of the jobs in the registry, and more. Below is an example using a StartedJobRegistry.

你可以获取到jobs注册的数量，jobs注册的id等，以下是使用`StartedJobRegistry`的示例。

```python
import time
from redis import Redis
from rq import Queue
from rq.registry import StartedJobRegistry
from somewhere import count_words_at_url

redis = Redis()
queue = Queue(connection=redis)
job = queue.enqueue(count_words_at_url, 'http://nvie.com')

# 通过queue获取StartedJobRegistry
registry = StartedJobRegistry(queue=queue)

# 或者queue名称获取StartedJobRegistry并且俩捏
registry2 = StartedJobRegistry(name='my_queue', connection=redis)

# 当job从queue移除的时候，休眠片刻
time.sleep(0.1)

print('Queue associated with the registry: %s' % registry.get_queue())
print('Number of jobs in registry %s' % registry.count)

# 从注册表中获取job id列表
print('IDs in registry %s' % registry.get_job_ids())

# 使用job实例或者job id，测试job是否在注册表中
print('Job in registry %s' % (job in registry))
print('Job in registry %s' % (job.id in registry))
```

1.2.0新功能

可以从`Queue`对象快速访问job 注册表
```python
from redis import Redis
from rq import Queue

redis = Redis()
queue = Queue(connection=redis)

queue.started_job_registry  # 返回 StartedJobRegistry
queue.deferred_job_registry   # 返回 DeferredJobRegistry
queue.finished_job_registry  # 返回 FinishedJobRegistry
queue.failed_job_registry  # 返回 FailedJobRegistry
queue.scheduled_job_registry  # 返回 ScheduledJobRegistry
```

## Removing Jobs(移除jobs)
1.2.0新功能

> 从job注册表中移除job，可以使用`registry.remove()`。当你要手动从注册表中删除job（例如在过期的job之前从中删除）时，此功能很有用FailedJobRegistry。

```python
from redis import Redis
from rq import Queue
from rq.registry import FailedJobRegistry

redis = Redis()
queue = Queue(connection=redis)
registry = FailedJobRegistry(queue=queue)

# 这就是如何从注册表中移除job
for job_id in registry.get_job_ids():
    registry.remove(job_id)

# 如果你想从注册表中移除，并且删除job的话
# 使用 `delete_job=True` 参数
for job_id in registry.get_job_ids():
    registry.remove(job_id, delete_job=True)
```