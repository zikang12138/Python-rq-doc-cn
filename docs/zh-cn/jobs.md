## Jobs

> 对某些情况下，从Job函数本身内部访问当前Job ID或实例可能很有用。或者存储Job上的任意数据。

## Job Creation (创建Job)
当你 enqueue 入列一个函数时，会返回一个job。然后可以访问 id 属性，该属性以后可用于检索Job。 (译者:之前也提到过，这里返回的是实例 是job的代理对象)
```python
from rq import Queue
from redis import Redis
from somewhere import count_words_at_url

redis_conn = Redis()
q = Queue(connection=redis_conn)  # no args implies the default queue

# 延时执行 count_words_at_url('http://nvie.com')
job = q.enqueue(count_words_at_url, 'http://nvie.com')
print('Job id: %s' % job.id)
```
或者，如果你需要预定的job ID，可以在创建作业时指定它。
```python
job = q.enqueue(count_words_at_url, 'http://nvie.com', job_id='my_job_id')
```

也可以直接用`Job.create()`创建job
```python
from rq.job import Job

job = Job.create(count_words_at_url, 'http://nvie.com')
print('Job id: %s' % job.id)
q.enqueue_job(job)

# 创建指定id的job
job = Job.create(count_words_at url, 'http://nvie.com', id='my_job_id')
```
`create()`函数的接收的参数有:
- `timeout`: 默认job执行的最大运行时间。`failed`单位默认是秒，参数可以是整数，也可以是表示整数的字符串，(如 2, "2")，
还可以是包含时间单元，小时，分钟，秒的字符串，如('1h', '3m', '5s')
(译者: 前面说到用enqueue创建job，超时时间参数都是`job_timeout`, 不明白为什么不统一参数)
- `result_ttl`: 指任务函数执行完毕后，结果保留的时间，单位为秒。过期后将会被自动删掉，默认为 500 秒。
- `ttl` 指任务被丢弃之前的最长排队时间，单位为秒, 此默认参数为: None 无限时常。
- `failure_ttl`: 指将失败的任务函数保留多长时间，默认保存一年时间。
- `depends_on`: 指在进入队列排队之前，必须完成的另外一个函数。(或者job id)
- `id`:可以手动指定job id  (译者：enqueue创建job使用job_id这个参数指定)
- `description`: 给job添加额外的描述
- `connection`:
- `status`:
- `origin`:
- `meta`: 可以包含自定义信息或状态的字典。（译者:比如job处理进度之类的，都可以存储到这里面）
- `args`和`kwargs`: 使用这些可以将任务函数参数，显式的传递过去。如果你的函数正好和RQ的参数冲突了，
就可以用这种方法。(如: `description`和`ttl`)。

最后一种情况，想把任务函数冲突的参数名，传递给任务函数而不是 RQ队列任务的话，可以这样这样做:
```python
job = Job.create(count_words_at_url,
          ttl=30,  # This ttl will be used by RQ
          args=('http://nvie.com',),
          kwargs={
              'description': 'Function description', # 这是传给 count_words_at_url 的参数
              'ttl': 15  # 这是传给 count_words_at_url函数的参数
          })
```
(译者: 整体和enqueue创建job，参数差不多区别不大，部分参数，官方文档为给出解释)

## Retrieving a Job from Redis (从redis中检索Job)

所有Job的信息都存储在redis里面在，可以通过`Job.fetch()`来检索Job及其属性。(译者：可以自行查看下连接的redis库，所有的信息redis都有，也可以自己按照格式查看)
```python
from redis import Redis
from rq.job import Job

redis = Redis()
job = Job.fetch('my_job_id', connection=redis)
print('Status: %s' % job.get_status())
```
一些有趣的job属性包括以下:
- `job.get_status()`: 返回值可能是`queued`，`started`，`deferred`，`finished`，和`failed`。（译者：job当前的各种状态分别对应 队列排队, 启动中，延迟执行， 完成， 失败）
- `job.func_name`:
- `job.args`: job函数传递的args参数
- `job.kwargs`: job函数传入的kwargs参数
- `job.result`: 这个属性能返回任务执行(job)结果，如果任务(job)未完成，会返回None，前提是任务函数(job)有返回值才行。当Job已执行且具有返回值或异常时，它将返回该值或异常。
回写到Redis的返回值，并且将根据result_ttl Job的参数过期（默认为500秒）
- `job.enqueued_at`
- `job.started_at`
- `job.ended_at`
- `job.exc_info`

如果要有效地获取大量作业，请使用Job.fetch_many()。

```python
jobs = Job.fetch_many(['foo_id', 'bar_id'], connection=redis)
for job in jobs:
    print('Job %s: %s' % (job.id, job.func_name))
```

## Accessing The “current” Job from within the job function（从Job函数内部访问当前Job）

由于job函数是常规的Python函数，因此必须检索Job才能检查或更新Job的属性。要从函数内部执行此操作，可以使用：
```python
from rq import get_current_job

def add(x, y):
    job = get_current_job()
    print('Current job: %s' % (job.id,))
    return x + y
```

请注意，在job函数的上下文之外调用get_current_job（）将返回None。

## Storing arbitrary data on jobs(在Job上存储任意数据)
在版本0.8.0中进行了改进。

要添加/更新有关此Job的自定义状态信息，可以访问 meta属性，该属性使可以在Job本身上存储任意可定制的数据：
(译者：我一般就是在这里添加 job函数进度，可以实时查看，方便前端制作进度条)
```python
import socket

def add(x, y):
    job = get_current_job()
    job.meta['handled_by'] = socket.gethostname()
    job.save_meta()

    # do more work
    time.sleep(1)
    return x + y

```
## Time to live for job in queue (Job在queue的生存时间)
版本0.4.7中的新功能。

作业具有两个TTL，一个用于Job结果，result_ttl另一个用于Job本身ttl。
如果有在一定时间后不应该执行的Job，则使用后者。
```python
# create创建job
job = Job.create(func=say_hello,
                 result_ttl=600,  # 保存Job（如果成功）及其结果的时间（秒）
                 ttl=43,  # Job被丢弃之前的最大排队时间（以秒为单位）。
                )

# 或者使用enqueue创建job
job = q.enqueue(count_words_at_url,
                'http://nvie.com',
                result_ttl=600,  # 保存Job（如果成功）及其结果的时间（秒）
                ttl=43  # 最大排队时间
               )
```

## Failed Jobs （失败的job）

如果job在执行过程中失败，则Job会被放入`FailedJobRegistry`中。在Job实例上，该is_failed属性为true。
可以通过访问`FailedJobRegistry` queue.failed_job_registry。
```python
from redis import StrictRedis
from rq import Queue
from rq.job import Job


def div_by_zero(x):
    return x / 0


connection = StrictRedis()
queue = Queue(connection=connection)
job = queue.enqueue(div_by_zero, 1)
registry = queue.failed_job_registry

worker = Worker([queue])
worker.work(burst=True)

assert len(registry) == 1  # 失败的job被保存在 FailedJobRegistry 中

registry.requeue(job)  # 将Job放到原始队列中

assert len(registry) == 0

assert queue.count == 1

```
默认情况下，失败的作业将保留1年。您可以通过failure_ttl在入队时指定（以秒为单位）来更改此设置 。

```python
job = queue.enqueue(foo_job, failure_ttl=300)  # 保存5分钟，单位为秒
```

## Requeueing Failed Jobs(重新入列失败的job)

RQ还提供了一个CLI工具，使重新排队失败的Job变得容易。
```python
# 这将会从myqueue失败的Job注册表中重新入队列 foo_job_id和bar_job_id
rq requeue --queue myqueue -u redis://localhost:6379 foo_job_id bar_job_id

# 这个命令将会把job注册表中所有失败的job重新排入队列
rq requeue --queue myqueue -u redis://localhost:6379 --all
```








