import asyncio

import nats


async def main():
    nc = await nats.connect()
    inbox = nc.new_inbox()
    is_done = asyncio.Future()

    async def subscribe_handler(msg):
        subject = msg.subject
        reply = msg.reply
        data = msg.data.decode()
        await nc.publish(msg.reply, "응디고양".encode(), reply=inbox)
        print(f"Received a message on {subject} {reply}: {data}")

    async def subscribe_handler2(msg):
        subject = msg.subject
        reply = msg.reply
        data = msg.data.decode()
        print(f"Received a message on {subject} {reply}: {data}")

    await nc.subscribe("foosexking9476928692", cb=subscribe_handler)
    await nc.subscribe(inbox, cb=subscribe_handler2)

    for i in range(0, 10):
        ack = await nc.publish("foosexking9476928692", f"hello world: {i}".encode(), reply=inbox)
        print(ack)

    await asyncio.wait_for(is_done, 5.0)
    print(inbox)
    await nc.close()


if __name__ == "__main__":
    asyncio.run(main())
