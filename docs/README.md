
## rq

> RQ(Redis Queue) 是一个非常简洁,轻量级,用于处理后台任务队列的Python库。

- `当前翻译版本2020年1月` [v1.0](https://github.com/rq/rq/releases/tag/v1.0)

## 特性 

- 简洁轻量级(对比Celery [stackoverflow](https://stackoverflow.com/questions/13440875/pros-and-cons-to-use-celery-vs-rq))。
- 方便集成到web应用当中,对新手友好。


## FQA
- `broker 仅支持redis`
- 不支持windows， 由于RQ worker只实现了`fork()`。

## 解释
- 消息生产者Producer：发送消息到消息队列。
- 消息消费者Consumer：从消息队列接收消息。
- Broker：概念来自与Apache ActiveMQ，指MQ的服务端，帮你把消息从发送端传送到接收端。
- 消息队列Queue：一个先进先出的消息存储区域。消息按照顺序发送接收，一旦消息被消费处理，该消息将从队列中删除。

## [快速开始](zh-cn/quickstart.md)

## 参考
- [计算机术语翻译](http://dict.cnki.net/dict_result.aspx?searchword=Burst%20Mode)
- [软件工程中英对照术语](https://people.ubuntu.com/~happyaron/l10n/%E8%BD%AF%E4%BB%B6%E5%B7%A5%E7%A8%8B%E4%B8%AD%E8%8B%B1%E5%AF%B9%E7%85%A7%E6%9C%AF%E8%AF%AD%E8%A1%A8-old.html)
- [翻译术语](https://github.com/dotnetcore/aspnetcore-doc-cn/wiki/%E7%BF%BB%E8%AF%91%E6%9C%AF%E8%AF%AD)
- https://stackoverflow.com/questions/13440875/pros-and-cons-to-use-celery-vs-rq (celery对比rq)
- https://juejin.im/post/5df8d054f265da33d21e7bce (消息队列简单介绍)
- https://www.quora.com/What-is-the-difference-between-RQ-redis-queue-and-Celery  (celery对比rq,需要fq)
- https://www.reddit.com/r/django/comments/974yn9/best_task_queue_and_message_broker_to_use/ (需要fq)


