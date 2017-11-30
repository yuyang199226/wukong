#! user/bin/env python
# -*- coding: utf-8 -*-
import redis
from django.conf import settings

class Singleton(object):
    def __new__(cls, *args, **kwargs):
        # 如果当前类没有_instance属性，那么就调用父类的__new__方法实例化对象，新增_instance属性并赋值
        if not hasattr(cls, "_instance"):
            cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance


class SingleRedis(Singleton):
    def __init__(self,):
        pool = redis.ConnectionPool(**settings.REDIS_PARAMETER)
        self.conn = redis.Redis(connection_pool=pool)
"""
a = SingleRedis()
print(a)  # <__main__.SingleRedis object at 0x0000017D31F8CCF8>
a.conn.hset('test', 'k', 'v')
print(a.conn.hget('test', 'k')) # b'v'

b = SingleRedis()
print(b)  # <__main__.SingleRedis object at 0x0000017D31F8CCF8>
print(b.conn.hget('test', 'k')) # b'v'

"""
