# echo-client.py
import ssl
import sys
import trio

# arbitrary, but:
# - must be in between 1024 and 65535
# - can't be in use by some other program on your computer
# - must match what we set in our echo server
PORT = 8443
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
# context.load_verify_locations('proxy.cert')
context.load_verify_locations('stunnel.pem')
pass
async def sender(client_stream):
    print("sender: started!")
    while True:
        data = b"async can sometimes be confusing, but I believe in you!"
        print(f"sender: sending {data!r}")
        await client_stream.send_all(data)
        await trio.sleep(1)

async def receiver(client_stream):
    print("receiver: started!")
    async for data in client_stream:
        print(f"receiver: got data {data!r}")
    print("receiver: connection closed")
    sys.exit()

async def parent():
    print(f"parent: connecting to 127.0.0.1:{PORT}")
    client_stream = await trio.open_ssl_over_tcp_stream("127.0.0.1", PORT,ssl_context=context)
    # client_stream = await trio.open_ssl_over_tcp_stream("wx.ccmo.cc", 443,)
    async with client_stream:
        async with trio.open_nursery() as nursery:
            print("parent: spawning sender...")
            nursery.start_soon(sender, client_stream)
            print("parent: spawning receiver...")
            nursery.start_soon(receiver, client_stream)

trio.run(parent)