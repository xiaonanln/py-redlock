# -*- coding: utf8 -*-

import random
import string
import time

class RedisKeyLocker(object):
	def __init__(self, redis):
		self.redis = redis
		self._unlockFunc = self.redis.register_script("""if redis.call("get",KEYS[1]) == ARGV[1] then
															    return redis.call("del",KEYS[1])
															else
															    return 0
															end
															""")

	def acquire(self, key, px, block=True):
		'''SET resource_name my_random_value NX PX 30000'''
		lockId = RedisKeyLocker._randomid()

		if block:
			while True:
				if self.redis.set(key, lockId, nx=True, px=px):
					return lockId
				else:
					time.sleep(0.01)
		else:
			if self.redis.set(key, lockId, nx=True, px=px):
				return lockId
			else:
				return None

	def release(self, key, lockId):
		self._unlockFunc(keys=[key], args=[lockId])

	@staticmethod
	def _randomid():
		return ''.join(random.sample(string.printable, 6))

	def key(self, key, px):
		return _Key(self, key, px)

class _Key(object):
	def __init__(self, owner, key, px):
		self.owner = owner
		self.key = key
		self.px = px
		self.lockId = None

	def acquire(self):
		self.lockId = self.owner.acquire(self.key, self.px)

	def release(self):
		if self.lockId:
			self.owner.release(self.key, self.lockId)
			self.lockId = None

	__enter__ = acquire

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.release()

if __name__ == '__main__':
	import redis
	rlm = RedisKeyLocker(redis.StrictRedis())
	lock_id = rlm.acquire("abc", 1000)
	print 'locked', lock_id
	rlm.release("abc", lock_id)
	print 'unlocked', lock_id

	lock_id = rlm.acquire("abc", 1000)
	print 'locked', lock_id
	lock_id = rlm.acquire("abc", 1000)
	print 'locked', lock_id
	rlm.release("abc", lock_id)
	print 'unlocked', lock_id

	lock_id = rlm.acquire("abc", 1000)
	print 'locked', lock_id
	rlm.release("abc", lock_id)
	print 'unlocked', lock_id