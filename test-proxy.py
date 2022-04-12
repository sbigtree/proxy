# echo-server.py

import trio
from itertools import count

# Port is arbitrary, but:
# - must be in between 1024 and 65535
# - can't be in use by some other program on your computer
# - must match what we set in our echo client
from trio._abc import SendStream, Stream

from _models import Header

PORT = 12345

CONNECTION_COUNTER = count()


async def sender(client_stream, forward_stream):
    print("sender: started!")

    async for data in client_stream:
        print(f"client_stream received data {data!r}")
        await forward_stream.send_all(data)
    print("client_stream: connection closed")



async def receiver(client_stream, forward_stream):
    async for data in forward_stream:
        print(f"forward_stream received data {data!r}")
        await client_stream.send_all(data)
    print("forward_stream: connection closed")


async def echo_server(server_stream: trio.SocketStream):
    # Assign each connection a unique number to make our debug prints easier
    # to understand when there are multiple simultaneous connections.
    ident = next(CONNECTION_COUNTER)
    print(f"echo_server {ident}: started")
    try:
        # b'CONNECT wx.ccmo.cc:443 HTTP/1.1\r\n
        # Host: wx.ccmo.cc:443\r\n
        # Proxy-Authorization: Basic YWRtaW46cXk4MzM0NjM0OA==\r\n
        # User-Agent: curl/7.76.1\r\n
        # Proxy-Connection: Keep-Alive\r\n\r\n'
        header = Header(await server_stream.receive_some())
        print(header.data)
        await server_stream.send_all(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        forward_stream: trio.SocketStream = await trio.open_tcp_stream(header.host, header.port)

        async with trio.open_nursery() as nursery:
            nursery.start_soon(sender, server_stream, forward_stream)
            nursery.start_soon(receiver, server_stream, forward_stream)

        print(f"echo_server {ident}: connection closed")
    # FIXME: add discussion of MultiErrors to the tutorial, and use
    # MultiError.catch here. (Not important in this case, but important if the
    # server code uses nurseries internally.)
    except Exception as exc:
        # Unhandled exceptions will propagate into our parent and take
        # down the whole program. If the exception is KeyboardInterrupt,
        # that's what we want, but otherwise maybe not...
        print(f"echo_server {ident}: crashed: {exc!r}")


async def main():
    await trio.serve_tcp(echo_server, PORT)


# We could also just write 'trio.run(trio.serve_tcp, echo_server, PORT)', but real
# programs almost always end up doing other stuff too and then we'd have to go
# back and factor it out into a separate function anyway. So it's simplest to
# just make it a standalone function from the beginning.
trio.run(main)
