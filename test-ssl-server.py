import ssl
from itertools import count

import trio

PORT = 8443
CONNECTION_COUNTER = count()
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
# context.load_cert_chain('./proxy.cert', 'proxy.key')
context.load_cert_chain('./server.cert', 'server.key')

# context.load_cert_chain('./stunnel.pem', './stunnel.pem')
async def echo_server(server_stream: trio.SSLStream):
    ident = next(CONNECTION_COUNTER)
    print(f"echo_server {ident}: started")
    try:
        async for data in server_stream:
            print(f"echo_server {ident}: received data {data!r}")
            content = b"HTTP/1.1 200 OK\r\n" \
                      b"Content-Type: */*\r\n" \
                      b"Content-Length: %d\r\n" \
                      b"Connection: close\r\n" \
                      b"\r\n" \
                      b"%s" % (len(data), data,)
            await server_stream.send_all(content)
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
    await trio.serve_ssl_over_tcp(echo_server, PORT, context, host="127.0.0.1")


if __name__ == '__main__':
    trio.run(main)
