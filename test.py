# tasks-intro.py
from itertools import count
from queue import Queue
import asyncio

import trio

aque = asyncio.Queue()
que = Queue()


async def consumer(task):
    """消费者"""
    # task =  aque.get_nowait()
    # print(f'取出一个任务{task}')
    await trio.sleep(2)
    print(f"{task} 执行完成!")


async def producer():
    """生产者"""
    print("生产者")
    counter = count()
    while True:
        index = next(counter)
        print(f'创建一个任务 {index}')
        await aque.put(index)
        await trio.sleep(0.5)


async def workshop():
    async with trio.open_nursery() as tasker:
        while not aque.empty():
            task = aque.get_nowait()
            tasker.start_soon(consumer, task)

async def heart():
    while True:
        await trio.sleep(1)
        print('heart connect')


async def worker():
    counter = count()
    while True:
        # for i in range(5):
        #     await trio.sleep(1)
        #     aque.put_nowait(next(counter))
        async with trio.open_nursery() as nursery:
            while not aque.empty():
                task = aque.get_nowait()
                try:
                    nursery.start_soon(consumer, task)
                except Exception as e:
                    print(e)

async def parent():
    print("parent: started!")
    async with trio.open_nursery() as nursery:
        nursery.start_soon(heart) # 心跳连接
        nursery.start_soon(producer) # 生产者，不断的生成产品
        nursery.start_soon(worker) # 消费者车间，不断的取出产品消费
        # while True:
        #
        #     nursery.start_soon(consumer, task)


trio.run(parent)
# trio.run(child1)
