from redis.asyncio import Redis as RedisClient

redis_client: RedisClient = RedisClient(decode_responses=True)


async def get_redis() -> RedisClient:
    return redis_client
