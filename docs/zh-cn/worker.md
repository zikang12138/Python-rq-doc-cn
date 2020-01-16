
> rq队列服务(Worker)是一个单独的Python进程，通常在后台运行，为处理任务(job)而存在，来执行您不想在Web进程内部执行的冗长或阻塞的任务。

!> (译者: worker:rq队列服务; job:待执行的任务函数或者类。后面我将不翻译直接用这两个单词感觉更准确）

## Starting Workers（启动Workers）
要启动rq队列服务，必须得从`项目目录的根目录下`启动。(译者：划重点，一定要从项目目录根目录下启动，否则会找不到文件路径，执行任务报错)
```python
$ rq worker high default low
*** Listening for work on high, default, low
Got send_newsletter('me@nvie.com') from default
Job ended normally without result
*** Listening for work on high, default, low
...
```
worker将会不停的从给定的队列中读取任务并执行，(顺序很重要)，当一个job完成后，才会去执行下一个任务(job)。

`注意`每个rq队列服务同一时间只会处理一个任务(job)。在工作进程中，一个worker不能并发处理任务。如果你要同时处理多个任务，可以添加更多的rq队列服务(worker)。

可以使用如[Supervisor](zh-cn/supervisor.md)或 systemd的流程管理器在生产中运行的worker。
(译者:开始的时候，我没注意到这一点，踩了一些坑。还有就是推荐Supervisor来托管多个 rq worker， 方便可靠简单好用。)


## Burst Mode (突发模式)
默认情况下，rq队列服务将会立即执行队列中的任务，并且执行完之后会等待新的任务。worker也可以开启突发模式，完成当前所有可用的的队列之后，并在清空所有给定队列后立即退出。
```python
$ rq worker --burst high default low
*** Listening for work on high, default, low
Got send_newsletter('me@nvie.com') from default
Job ended normally without result
No more work, burst finished.
Registering death.
```
这对于需要定期处理的批处理job很有用，或者仅在高峰期临时扩大worker处理任务能力时，这可能很有用。

## Worker Arguments（rq队列服务启动参数）
除了`--burst`参数之外，`rq worker`还能接收以下的参数。
- `--url`或`-u`:指定redis连接信息的URL，(如`rq worker --url redis://:secrets@example.com:1234/9` 或者`rq worker --url unix:///var/run/redis/redis.sock`)
(译者：如果直接rq worker启动，redis连接都是指默认本地的，队列名称为`default`，对我来说都会指定redis URL来启动)
- `--path`或`-P`:支持多个导入路径（例如rq worker --path foo --path bar）
- `--config`或`-c`:包含RQ设置的模块的路径。
- `--results-ttl`：任务结果将保留的时间。（单位秒,默认为500)(译者:超过这个时间会删除任务返回结果,前提是任务函数有返回值)。
- `--worker-class`或`-w`:要使用的RQ Worker Class（例如rq worker --worker-class 'foo.bar.MyWorker'）
- `--job-class`或`-j`：要使用的RQ 任务(job) Class。（译者:之前一直说的是任务函数，也可以传任务类).
- `--queue-class`：要使用的RQ Queue类.
- `--connection-class`：要使用的Redis连接类，默认为redis.StrictRedis.
- `--log-format`：工作日志的格式，默认为 '%(asctime)s %(message)s'.
- `--date-format`：工作日志的日期时间格式，默认为 '%H:%M:%S'.
- `--disable-job-desc-logging`：关闭作业描述日志记录。
- `--max-jobs`：要执行的最大任务数。(译者:这个参数我使用过，一旦处理的任务数超过这个参数，rq队列服务(worker)就会结束进程退出)

## Inside the worker （rq队列服务(worker)内部）

#### The Worker Lifecycle（worker服务生命周期）

rq队列服务(worker)的生命周期包含以下几个阶段。
- 1 开启(Boot),加载Python环境。
- 2 启动注册(Birth registration),worker服务将它本身注册到系统，以便知道运行状况.
- 3 开始监听(Start listening),从任意队列中弹出任务(job)，如果队列是空的，则rq队列服务(worker)以Burst Mode(突发模式)运行，这时可以退出，否则就会继续等待任务(job)的到来。
- 4 准备执行任务(Prepare job execution),rq队列服务通过设置状态为`busy`告诉系统开始执行任务(job)了，并且把任务(job)注册到`StartedJobRegistry`.
- 5 分叉一个子进程(Fork a child process), 分叉一个子进程(the “work horse”)在一个安全的环境下，默默的执行任务函数。(译者:此时即使停止RQ队列服务，任务也会接着执行完)
- 6 处理工作(Process work) 在子进程(work horse)中默默执行任务(job)。(译者:`work horse`俚语，大概意思就是默默做事，埋头苦干。)
- 7 清理执行任务(Cleanup job execution), rq队列服务(worker)设置它的状态为`idle`,并且以`result_ttl`参数，把结果设置为过期。同样任务(job)会从`StartedJobRegistry`移除，如果任务函数执行完毕没有异常终止，就会添加到`FinishedJobRegistry`,否则就添加到`FailedJobRegistry`.
- 8 循环(Loop)，从第三步开始执行。

(译者:一个任务函数或者类，是可以重复推入队列的，推入队列的时候指定一个job_id，依据这个可以去`StartedJobRegistry`里面查看此任务job是否正在执行，避免重复执行一个任务)。


## Performance Notes(性能说明)
`rq worker`shell脚本基本上是一个简单的 取-分叉-执行 循环(fetch-fork-execute loop),如果大量的任务(job)执行需要很多步骤，或者它们都依赖于同一组模块，则每次运行一项工作时，都需要占用一些资源（因为您是在分叉之后进行导入）。这很安全，因为RQ不会以这种方式泄漏内存，但是速度也很慢。

可以用来提高此类作业的吞吐量性能的模式可以是在派生之前导入必要的模块。无法告诉RQ队列服务(worker)执行此设置，但是可以在开始工作循环之前自己进行操作。

可以这样做，而不是使用`rq worker`, 一个简单的实现演示。
```python
#!/usr/bin/env python
import sys
from rq import Connection, Worker

# 预加载库
import library_that_you_want_preloaded

# ,
# 提供需要监听的队列名称作为脚本的参数
# 类似 rq worker
with Connection():
    qs = sys.argv[1:] or ['default']

    w = Worker(qs)
    w.work()
```

## Worker Names(RQ队列服务名称)
rq队列服务(Worker)实例化的时候会随机生成一个名称，以此注册到系统。请参考[Monitoring/监控](zh-cn/monitoring.md),要覆盖默认值，可以在启动的时候指定名称，或者用`--name`选项传入。

(译者: 从Queue()这个对象源码中的缺省参数name='default'可以看出来，队列名不是随机的，不传值默认就叫`default`，不确定文档描述是否准确)
```python
from redis import Redis
from rq import Queue, Worker

redis = Redis()
queue = Queue('queue_name')

# Start a worker with a custom name
worker = Worker([queue], connection=redis, name='foo')
```

## Retrieving Worker Information(检索RQ队列(worker)服务信息)
在版本0.10.0中更新。

`Worker`实例会将其运行时信息存储在Redis中。检索方法如下：
```python
from redis import Redis
from rq import Queue, Worker

# 返回这个连接中,所有的worker注册
redis = Redis()
workers = Worker.all(connection=redis)

# 返回这个队列中所有的worker (new in version 0.10.0)
queue = Queue('queue_name')
workers = Worker.all(queue=queue)
worker = workers[0]
print(worker.name)
```
除之外worker.name，worker还有以下属性.
- `hostname` -运行此工作程序的主机
- `pid` -worker的进程ID
- `queues` -该worker在侦听的队列
- `state`-可能的状态是suspended，started，busy和idle
- `current_job` -当前正在执行的任务(job)（如果有）
- `last_heartbeat` -上次见到该worker的时间。(译者:我理解为最近执行时间)
- `birth_date` -Worker实例化的时间
- `successful_job_count` -成功完成任务(job)的数量
- `failed_job_count` -执行任务(job)失败的数量
- `total_working_time` -执行任务(job)所花费的时间，以秒为单位

版本0.10.0中的新功能。

如果只想知道正在监听的worker的数量， `Worker.count()`性能会更高。
```python
from redis import Redis
from rq import Worker

redis = Redis()

# 从这个redis连接中获取 worker的数量
workers = Worker.count(connection=redis)

# 从指定的队列中获取 worker的数量
queue = Queue('queue_name', connection=redis)
workers = Worker.all(queue=queue)
```
## Worker Statistics(Worker统计)
0.9.0版中的新功能。

如果要检查队列的利用率，Worker实例将存储一些有用的信息：
```python
from rq.worker import Worker
worker = Worker.find_by_key('rq:worker:name')

worker.successful_job_count  # 执行成功的数量
worker.failed_job_count # 执行失败异常的数量
worker.total_working_time  # 执行耗时 (单位秒)
```

## Better worker process title (更好的worker进程标题)
安装第三方软件包后，Worker进程的标题将更好（如ps和top等系统工具所显示）`setproctitle`：
```python
pip install setproctitle
```
## Taking Down Workers (停止Workers)
任何时间内, Worker收到`SIGINT`(ctrl+C指令),或者`SIGTERM`(系统kill)，worker都会将当前的job运行结束,然后停止循环和正常注册此worker的结束。

如果在此下架阶段`SIGINT`或`SIGTERM`再次被接收，worker将强制终止子进程（发送SIGKILL），但仍将尝试记录其自身的死亡。

(译者: 即使强制kill掉worker，当前正在执行的job也会继续执行完毕，之后此worker才会正常退出，最终也会在redis存下此worker的信息)

## Using a Config File(使用配置文件)
如果你想`rq worker`通过配置文件而不是通过命令行参数进行配置，可以通过创建一个Python文件来实现 `settings.py`：
```python
REDIS_URL = 'redis://localhost:6379/1'

# 同样也可以这样去指定 Redis db
# REDIS_HOST = 'redis.example.com'
# REDIS_PORT = 6380
# REDIS_DB = 3
# REDIS_PASSWORD = 'very secret'

# Queues队列监听
QUEUES = ['high', 'default', 'low']

# 如果想用 `sentry` 收集运行异常的话， 可以这样做。
# 只需要为 RQ 配置这一步就行
# raven 必须得加 'sync+' 这个前缀 : https://github.com/nvie/rq/issues/350#issuecomment-43592410
SENTRY_DSN = 'sync+http://public:secret@example.com/1'

# 如果你想给 worker 取名的话，可以这样做
# NAME = 'worker-1024'

```
上面的示例显示了当前支持的所有选项。

注意： QUEUES 和 REDIS_PASSWORD 设置是从0.3.3开始的新设置。

要指定从哪个模块读取设置，请使用以下-c选项：

```python

$ rq worker -c settings

```

## Custom Worker Classes (自定义Worker类)
很多时候，可以自定义 Worker的行为(behavior), 目前为止(v1.0版本),一些常见的需求如下：
- 1 在运行 job 之前，管理数据库连接.
- 2 使用不需要`os.forck`的 model 执行 job.
- 3 使用不同的并发模型（例如 `multiprocessing` or `gevent`)。

你可以使用 `-w` 选项指定要使用的其他Worker Classes：
```python
$ rq worker -w 'path.to.GeventWorker'
```

## Custom Job and Queue Classes (自定义 Job 和 Queue 类)
你可以告诉worker, 使用  `--job-class` and/or `--queue-class` 自定义 Job 和 Queue 类

入队列时不要忘记使用那些相同的类。
如:
```python
from rq import Queue
from rq.job import Job

class CustomJob(Job):
    pass

class CustomQueue(Queue):
    job_class = CustomJob

queue = CustomQueue('default', connection=redis_conn)
queue.enqueue(some_func)
```

## Custom DeathPenalty Classes (自定义 结束处理机制 类) 
当job运行超时时，会自动调用`death_penalty_class`(default: UnixSignalDeathPenalty) 杀死它。
(译者: v1.0源码中Queue类默认全局处理Job超时时间为180秒, DEFAULT_TIMEOUT = 180, 当然使用enqueue方法入队列的时候，
也可以针对Job指定`job_timeout`参数)

当然这个方法可以被覆盖，如果你想以特定于应用程序或“更干净”的方式 Kill Job

使用以下参数构造DeathPenalty类 `BaseDeathPenalty(timeout, JobTimeoutException, job_id=job.id)`.

## Custom Exception Handlers (自定义异常处理)
如果你需要针对不同类型的作业以不同方式处理错误，或者只是想自定义RQ的默认错误处理行为，请rq worker使用以下`--exception-handler`选项运行：
```python
$ rq worker --exception-handler 'path.to.my.ErrorHandler'

# 多重异常处理同样也支持
$ rq worker --exception-handler 'path.to.my.ErrorHandler' --exception-handler 'another.ErrorHandler'

```
如果你想禁用RQ默认的异常处理，可以使用 `--disable-default-exception-handler` 选项

```python
$ rq worker --exception-handler 'path.to.my.ErrorHandler' --disable-default-exception-handler

```
