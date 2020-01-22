## Results

> Job 进入队列是函数调用延迟处理, 这意味着我们正在处理这个问题，但也得到了一些返回


## Dealing with Results (处理结果)

Python 函数可能会有返回值，所以Job也可以有，如果Job返回非`None`值, Worker 将会把返回值记录在Job Redis hash key之下。
Job的Redis hash值会有默认500秒时间, 默认Job完成之后开始。(译者:过期将会删除)

入队列将会把`Job`实例作为结果返回，像这样的Job对象是一个绑定job id的代理对象，以便于轮询结果。

在返回值的TTL上，返回值以有限的生命周期(通过redis过期key)会被写回到Redis， 这是为了避免Redis数据库不断增长。

从RQ >= 0.3.1起，可以使用`result_ttl`关键字参数 `enqueue()`和 `enqueue_call()`调用指定Job结果的TTL值。
它也可以用来完全禁用到期时间。然后,你将自己负责清理作业，因此请谨慎使用。

你可以像下面那样做
```python
q.enqueue(foo)  # 结果默认在500秒之后过期
q.enqueue(foo, result_ttl=86400)  # 结果在一天后过期
q.enqueue(foo, result_ttl=0)  # 结果将会被立即删除
q.enqueue(foo, result_ttl=-1)  # 结果不会自动删除， 你可以手动删除

```
此外，也可以使用它来保留没有返回值的已完成作业，默认情况下会立即将其删除。

```python
q.enqueue(func_without_rv, result_ttl=500)  # Job 会确定保留

```

## Dealing with Exceptions (处理异常)
Job可能会失败从而引发异常，This is a fact of life。RQ通常以下方式进行处理。

此外，应该可以重试失败的Job。通常需要手动解释，因为没有自动或可靠的方法让RQ判断重试某些任务是否安全。

当Job中引发异常时，该异常会被Worker服务捕获，序列化并存储在作业的Redis哈希exc_info键下。
把Job的引用放在FailedJobRegistry。默认情况下，失败的Job将保留1年。

Job本身具有一些可用于辅助检查的有用属性：
- Job的原始创建时间
- 最后入队日期
- 原始队列
- 所需功能调用的描述信息
- 异常信息

这样就可以手动检查和解释问题，并可能重新提交作业。

## Dealing with Interruptions(处理中断)
当Worker被友好的方式(`ctrl+C`或者 `kill`)杀死时，RQ会努力不丢失任何Job。当前Job完成后，Worker将停止进一步处理Job。
这样可以确保Job总是有公平的机会完成自己的Job。 (译者: 之前也说过，就是worker服务被ctrl+c或者kill命令终止，都会处理完当前正在处理的Job,但是等待中的Job将不会继续执行)

但是，可以用强行杀死Worker`kill -9`，这不会给Worker以优雅地完成Job或将Job failed 排队的机会。因此，强行杀死Worker可能会潜在的导致损坏。

Just sayin’. (译者: 只是提醒一下，一般情况下不要 强行 kill)

## Dealing with Job Timeouts (处理Job超时)
默认情况下，Job应在180秒内执行。超时后Worker将会杀死这个执行中的work horse(也就是job)，并将作业放入failed队列，表明作业已超时。

(译者: work horse 俚语，辛勤工作,埋头苦干,勤奋工作)

如果Job需要更多(或更少)的时间来完成，可以通过将其指定为enqueue()调用的关键字参数来延长（或缩短）默认超时时间 ，如下所示：
```python
q = Queue()
q.enqueue(mytask, args=(foo,), kwargs={'bar': qux}, job_timeout=600)  # job_timeout参数设置10 分钟
```

还可以更改通过特定队列实例立即入队的作业的默认超时，这对于以下模式很有用：
```python
# high队列 优先级应该在8秒结束, 而 low队列任务应该在10分钟结束
high = Queue('high', default_timeout=8)  # 8 secs
low = Queue('low', default_timeout=600)  # 10 mins

# 单独的Job 超时时间能够覆盖，默认的设置
low.enqueue(really_really_slow, job_timeout=3600)  # 1 hr
```

单独的Job仍可以指定其超时时间，因为Worker会以这些超时时间为准。









