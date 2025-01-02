
> 一个任务(job)是一个Python对象，表示 rq队列服务(Worker) 后台异步处理的函数。
只需要简单的将函数及其参数，推入到队列当中，就能异步调用。这个就叫做入队(enqueueing)

## Enqueueing Jobs(任务入队)

> 首先定义一个函数，将这个任务推入到队列当中
```python
import requests

def count_words_at_url(url):
    resp = requests.get(url)
    return len(resp.text.split())
```
看到了吧，这个函数没有任何特别得地方，所有Python函数都能放在队列中调用。
将此函数和url参数推到队列，后台执行，只需要以下简单的几步。

```python
from rq import Queue
from redis import Redis
from somewhere import count_words_at_url
import time

# 告诉rq用那个redis连接
redis_conn = Redis()
q = Queue(connection=redis_conn)  # 没有参数连接默认队列

# 延迟执行函数count_words_at_url
job = q.enqueue(count_words_at_url, 'http://nvie.com')
print(job.result)   # => None

# 现在等一下，知道rq队列服务(worker)把函数执行完毕。
time.sleep(2)
print(job.result)   # => 889

```
如果要将任务(job)推入特定的队列中，只需要指定其名称即可，就像这样
```python
q = Queue('low', connection=redis_conn)  # low 为rq队列服务(worker)名称
q.enqueue(count_words_at_url, 'http://nvie.com')
```
注意到上面例子中的 `Queue('low')`吗？你可以使用任何队列名，所以你可以比较灵活的去命名。
一种常见的命名模式是根据优先级命名队列。(例如: high, medium, low)

此外，你也可以传一些参数修改队列的行为。默认情况下，这些参数由kwargs传给rq任务队列。

- `job_timeout`: 指定任务函数最长运行完成时间 (超过默认时间未执行完会自动异常终止)，其默认单位为秒。参数可以是整数，也可以是表示整数的
字符串,(如 2, "2"), 还可以是包含时间单元，小时，分钟，秒的字符串，如('1h', '3m', '5s')
- `result_ttl`: 指任务函数执行完毕后，结果保留的时间，单位为秒。过期后将会被自动删掉，默认为 500 秒。
- `ttl`: 指任务被丢弃之前的最长排队时间，单位为秒, 此默认参数为: `None` 无限时常。
- `failure_ttl`: 指将失败的任务函数保留多长时间，默认保存一年时间。
- `depends_on`: 指在进入队列排队之前，必须完成的另外一个函数。(或者job_id)
- `job_id`: 可以手动指定函数的任务id。
- `at_front`: 会优先将此任务放到队列排队的前面执行，而不是后面。
- `description`: 为排队的任务函数添加的描述。
- `args`和`kwargs`: 使用这些可以将任务函数参数，显式的传递过去。如果你的函数正好和RQ的参数冲突了，
就可以用这种方法。(如: `description`和`ttl`)。

最后一种情况，想把任务函数冲突的参数名，传递给任务函数而不是 RQ队列任务的话，可以这样这样做:

```python
q = Queue('low', connection=redis_conn)
q.enqueue(count_words_at_url,
          ttl=30,  # 这个将会传给 RQ 使用
          args=('http://nvie.com',),
          kwargs={
              'description': 'Function description', # 这个会传给count_words_at_url函数
              'ttl': 15  # 这个也会传给 count_words_at_url 函数
          })
```

对于web进程无法直接访问Work进程中运行的源代码（即代码库X从代码库Y调用延迟的函数），也可以将该函数作为字符串引用传递。
(Tip: code base: 我翻译成代码库，[参考](https://blog.csdn.net/u012814856/article/details/89669857))


## Working with Queues(队列的使用)
除了 enqueue 启动任务函数外，还有一些经常用的方法。
```python

from rq import Queue
from redis import Redis

redis_conn = Redis()
q = Queue(connection=redis_conn)

# 可以取到队列中的 任务(job)数量
print(len(q))

# 队列相关操作
queued_job_ids = q.job_ids # 从队列中获取任务(job)id的列表
queued_jobs = q.jobs # 从队列中获取队列任务(job)实例的列表
job = q.fetch_job('my_id') # 返回一个任务(job) id 为 'my_id'的实例

# 清空队列，这个将会删除所有的队列中的任务(job)
q.empty()

# 删除队列
q.delete(delete_jobs=True) # 传入 True 将会移除队列中所有的任务(job)
# 队列就不会继续执行，仍然可以通过 enqueue 来重新创建

``` 

## On the Design（对于设计哲学）
使用RQ，不用预先为队列设定任何 channels(方法), exchanges(不确定翻译成什么),  routing rules(路由规则)或者其他。就可以将任务(job)推入任何队列当中，如果推入的队列不存在，将会立即创建。(个人理解:队列是有名字的，默认创建的为default,然后你在推到名为`your_q`队列，这时`your_q`这
个队列就会自动创建)

RQ没有使用高级的`broker`作为消息路由,(目前broker只支持rq, broker名词解释见翻译文档首页), 或许你会认为这是一个非常棒的优点或者缺点，但是我想这个取决与你正在解决的问题。

最后，它不是一个可移植的协议，因为它依赖 [pickle](https://docs.python.org/3/library/pickle.html) 来序列化任务(jobs),所以它只支持Python体系。

## The delayed result(延迟的结果)
当任务(job)推入队列时，`queue.enqueue()`方法会返回一个任务(job)实例，是一个能检查实际任务(job)执行结果的代理对象。

所以这个实例的`result`属性能返回任务执行(job)结果，如果任务(job)未完成，会返回`None`，前提是任务函数(job)有返回值才行。


## The @job decorator (@job装饰器)
如果你熟悉celery的话，你会习惯用`@task`装饰器。从RQ>0.3版本后，存在类似的装饰器。
```python
from rq.decorators import job

@job('low', connection=my_redis_conn, timeout=5)
def add(x, y):
    return x + y

job = add.delay(3, 4)
time.sleep(1)
print(job.result)
```

## Bypassing workers (绕过workers测试)
出于测试的目的，可以不用把任务传递给rq队列服务，直接进入队列执行任务函(从0.3.1版本之后)。所以你得将`is_async=False`参数传递给`Queue`的构造函数。
```python
>>> q = Queue('low', is_async=False, connection=my_redis_conn)
>>> job = q.enqueue(fib, 8)
>>> job.result
21
```
上面的代码，在没有rq服务启动的情况下，仍然能够运行，并且fib(8) 在同一进程中同步执行，你可以从Celery作为`ALWAYS_EAGER`知道这种操作。但是注意，仍然要和Redis实例建立有效的连接，以此来存储任务执行和完成相关的状态。

## Job dependencies(任务依赖)
RQ 0.4.0中的新功能是可以链接多个任务(job)的执行, 要依赖另一个任务函数执行的任务函数，可以传递`depends_on`参数。
```python
q = Queue('low', connection=my_redis_conn)
report_job = q.enqueue(generate_report)
q.enqueue(send_report, depends_on=report_job)
```
处理任务依赖性的能力可以将一个复杂的任务拆分为几个较小的任务。依赖于另一个任务的任务仅在其依赖关系成功完成时才入队列。

## Job Callbacks
New in version 1.9.0.
如果你需要在任务完成、失败或者停止时执行某个函数，RQ提供了`on_success`、`on_failure`和`on_stopped`回调。
### Callback Class and Callback Timeouts 


## The worker (rq队列服务)
想了解更多`worker`，可以参阅[Worker](zh-cn/worker.md)
RQ 允许您配置每个回调的方法和超时 - 成功、失败和停止。
要配置回调超时，请使用 接受和参数的RQ`Callback`对象。例如：`func` `timeout`
```python
from rq import Callback
queue.enqueue(say_hello, 
              on_success=Callback(report_success),  # default callback timeout (60 seconds) 
              on_failure=Callback(report_failure, timeout=10), # 10 seconds timeout
              on_stopped=Callback(report_stopped, timeout="2m")) # 2 minute timeout
```
### Success Callback
成功的回调必须时一个接受`job`, `connection` 和 `result`这三个参数的一个函数。你的函数应该接受`*args`和`**kwargs`以确保你的应用不会因为函数被添加额外的参数而中断。
```python
def report_success(job, connection, result, *args, **kwargs):
    pass
```
成功回调在作业执行完成后、依赖项入队之前执行。如果在执行回调时发生异常，作业状态将设置为`FAILED`，依赖性项不会入队。

回调的执行时间限制为 60 秒。如果要执行长时间运行的作业，请考虑使用 RQ 的作业依赖性功能。

## Considerations for jobs(任务注意事项)
从技术上讲，您可以将任何Python函数放在队列中调用，但这并不意味着这样做总是明智的。将任务放入队列之前要考虑的一些事项：
- 确保该功能`__module__`可以由任务函数导入。特别是，这意味着不能将`__main__`模块中声明的函数加入队列。
- 确保任务函数和rq服务共享完全相同的源代码。(译者解释:启动rq服务的时候，文件目录一定要一样，否则将会找不到执行函数)
- 确保函数调用不依赖于其上下文。特别是，全局变量是 evil(邪恶的)，但是当`Wroker`服务处理它时，函数所依赖的任何状态（例如“当前”用户或“当前” Web请求）都不存在。如果要为“当前”用户完成任务，则应将该用户解析为具体实例，并将对该用户对象的引用作为参数传递给作业。
(译者：最后一条注意事项在Flask应用中体现的很好，比如需要在任务(job)函数中，使用flask的app对象的时候，就需要app对象的引用传递进去)

## Limitations（局限性）
RQ服务仅在实现的系统上运行fork()。最值得注意的是，这意味着如果不使用Linux的Windows子系统并且无法在bash shell中运行，就无法在Windows上运行工作进程。
(译者:总结就就一句话: windows不能使用RQ服务)
