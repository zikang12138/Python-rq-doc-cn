#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/1/9 13:25
# @Author  : wgPython
# @File    : quickstart_main.py
# @Software: PyCharm
# @Desc    :
"""
入门演示主文件, 本人已亲自验证通过

首页例子
https://python-rq.org/

稍微有点区别：
因为我个人电脑没有安装redis，所以直接连接的服务器上的redis
注意 redis 连接地址，数据库index 都要一致
"""

from rq import Queue
from redis import Redis

from my_module import count_words_at_url  # 倒入自定义的job函数 后面我喜欢翻译成任务

# 注意这里连接的 redis 和 rq 服务的redis地址要一致
q = Queue(connection=Redis(host='xxx', password='xxx', port=6379, db=0))


result = q.enqueue(count_words_at_url, 'http://www.baidu.com')  # 我改成百度了

# rq 服务启动命令 我是用的服务器上的redis 不加默认连接本地
"""
# 注意在当前目录下运行次命令，以免rq服务找不到文件正确路径
rq worker --url redis://:password@ip:port/db

"""
