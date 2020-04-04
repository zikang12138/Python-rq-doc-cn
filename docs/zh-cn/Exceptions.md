> 由于发生异常，job可能会失败。当你的RQ worker在后台运行时，如何获得这些异常的通知？

## Default: the FailedJobRegistry(默认 )

RQ的默认安全网是FailedJobRegistry。每个未成功执行的job及其异常信息（类型，值，回溯）都存储在此处。尽管这可以确保没有失败的job“丢失”，但这对于主动通知job失败没有任何用处。


## Custom Exception Handlers(自定义异常处理)

> RQ支持注册自定义异常处理程序。这样就可以将自己的错误处理逻辑注入到worker中。

> 这是向RQ worker注册自定义异常处理程序的方式：
```python
from exception_handlers import foo_handler, bar_handler

w = Worker([q], exception_handlers=[foo_handler, bar_handler])
```
> handler本身是一个函数，采用下列参数：`job`， `exc_type`，`exc_value`和`traceback`：
```python
def my_handler(job, exc_type, exc_value, traceback):
    # 在这自定义处理
    # 例如，把异常信息写到数据库

```
你可能还会看到三个异常参数编码为：
```python
def my_handler(job, *exc_info):
    # do custom things here
```

```python
from exception_handlers import foo_handler

w = Worker([q], exception_handlers=[foo_handler],
           disable_default_exception_handler=True)
```

## Chaining Exception Handlers(链接异常处理)

> 处理程序本身负责确定是否完成了异常处理，还是应该落入堆栈中的下一个处理程序。处理程序可以通过返回布尔值来表明这一点。False表示停止处理异常，True表示继续并进入堆栈中的下一个异常处理程序。

> 对于实现者来说，重要的是要知道，默认情况下，当处理程序没有显式的返回值（因此None）时，它将被解释为True（即继续下一个处理程序）。

> 为了防止执行该处理程序链中的下一个异常处理程序，请使用不存在的自定义异常处理程序，例如：
```python
def black_hole(job, *exc_info):
    return False
```