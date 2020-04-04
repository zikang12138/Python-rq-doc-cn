监控是RQ的亮点。

这是很容易方式使用[rq控制面板](https://github.com/nvie/rq-dashboard)，这是一个单独分发的工具，它是RQ的轻量级基于Web的监视器前端，如下所示：

![图片](https://python-rq.org/img/dashboard.png)

安装只需要以下操作
```python

$ pip install rq-dashboard
$ rq-dashboard

```

同样它也可以很容易集成到Flask应用中去。


## Monitoring at the console(在控制台上监控)

> 要查看存在哪些队列以及哪些worker处于激活状态，只需要输入`rq info`：

```python
$ rq info
high       |██████████████████████████ 20
low        |██████████████ 12
default    |█████████ 8
3 queues, 45 jobs total

Bricktop.19233 idle: low
Bricktop.19232 idle: high, default, low
Bricktop.18349 idle: default
3 workers, 3 queues
```

## Querying by queue names(通过队列名称查询)

> 可以查询队列的子集，还可以查询特定的一个队列。

```python
$ rq info high default
high       |██████████████████████████ 20
default    |█████████ 8
2 queues, 28 jobs total

Bricktop.19232 idle: high, default
Bricktop.18349 idle: default
2 workers, 2 queues
```

## Organising workers by queue(通过队列组织workers)

> 默认情况下，`rq info`会打印当前活动的worker和正在监控的queues，就像这样：
```python
$ rq info
...

Mickey.26421 idle: high, default
Bricktop.25458 busy: high, default, low
Turkish.25812 busy: high, default
3 workers, 3 queues
```

> 要查看相同的数据，但按队列组织，可以使用-R（或--by-queue）标志：
```python
$ rq info -R
...

high:    Bricktop.25458 (busy), Mickey.26421 (idle), Turkish.25812 (busy)
low:     Bricktop.25458 (busy)
default: Bricktop.25458 (busy), Mickey.26421 (idle), Turkish.25812 (busy)
failed:  –
3 workers, 4 queues
```

## Interval polling(间隔轮询)

> 默认情况下，`rq info`将打印统计信息然后退出。还可以使用该--interval标志指定轮询间隔。
```python
$ rq info --interval 1
```

> rq info现在将每秒更新一次屏幕。您可以指定浮点值来表示秒的分数。请注意，低间隔值当然会增加Redis的负载。
```python
$ rq info --interval 0.5
```

