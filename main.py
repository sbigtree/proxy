import base64
import socket
import sys
import typing
from itertools import count

import trio
from urllib3.util.url import URI_RE

from log import log
from log.logger import init_logger
from _models import Url, Header

init_logger('proxy', debug=True, )


class Proxy:
    def __init__(self, password):
        self.counter = count()
        self.password = password

    async def client2forwarder(self, client: trio.SocketStream, forwarder: trio.SocketStream):
        """客户端 到 转发
        """
        async for data in client:
            # 接收client的要转发的数据
            # log.info(f'recv: {data!r}')
            await forwarder.send_all(data)
        # await forwarder.aclose()
        log.info(f'{client.socket.getsockname()} client接收完成')

    async def forwarder2client(self, forwarder: trio.SocketStream, client: trio.SocketStream):
        """转发者 到 客户端
        """
        async for data in forwarder:
            # 接收转发着的数据
            log.info(f'recv: {data!r}')
            await client.send_all(data)
            if data == b'':
                log.info(f'{forwarder.socket.getsockname()} forwarder接收完成')
                return
        await forwarder.aclose()

    async def handle(self, conn: trio.SocketStream, *args, **kwargs):
        """
        处理请求
        """
        ident = next(self.counter)
        log.info(f"echo_server {ident}: started")
        addr = conn.socket.getpeername()
        addr2 = conn.socket.getsockname()
        try:
            # 链接进来的的第一次数据，请求头
            data = await conn.receive_some()
            header = Header(data)
            # 转发数据
            # http  b'GET http://steamcommunity.com/ HTTP/1.1\r\nHost: steamcommunity.com\r\nUser-Agent: curl/7.76.1\r\nAccept: */*\r\nProxy-Connection: Keep-Alive\r\n\r\n'
            # https b'CONNECT steamcommunity.com:443 HTTP/1.1\r\nHost: steamcommunity.com:443\r\nUser-Agent: curl/7.76.1\r\nProxy-Connection: Keep-Alive\r\n\r\n'
            # 如果是http请求，服务端收到请求后会直接响应数据，响应头包含了Content-Length  和 Connection: close,客户端会断开链接
            # 创建转发新连接
            authorization = header.headers.get('Proxy-Authorization')
            try:
                # authorization = authorization.split(' ')[1].encode()
                if not header.proxy_host:
                    auth = base64.b64decode(authorization.split(' ')[1].encode()).decode('utf8')
                    # log.info(f'auth {auth}  {self.password}')
                    if auth != f'{self.password}:{self.password}':
                        raise ValueError('authorization')

            except Exception:
                data = b"HTTP/1.1 407 authorization\r\nContent-Type: */*\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
                await conn.send_all(data)
                # await conn.aclose()
            # log.info(authorization)
            if header.is_ssl:
                # proxy = header.headers.get('proxy')
                # 源客户端 => 中转代理 => 代理 => 目标server
                if header.proxy_host and header.proxy_port:
                    # 源客户端 => 中转代理 => 代理
                    # conn = 源客户端
                    # forwarder = 代理
                    # 如果有二级代理，连接下一个代理
                    data = b"HTTP/1.1 200 Connection Established\r\n\r\n"
                    await conn.send_all(data)
                    # conn对应的是上一级的转发客户端
                    forwarder: trio.SocketStream = await trio.open_tcp_stream(header.proxy_host, header.proxy_port)
                    header.headers.pop('proxy')
                    header.headers.update({'proxy2': '1'})  # 告诉下一个代理，我是中转代理，不需要建立ssl握手
                    data = [b'%s: %s' % (item[0], item[1]) for item in header.headers.raw]
                    data.insert(0, header.line0)
                    data = b'\r\n'.join(data)
                    data = b'%s\r\n\r\n' % data
                    # 发送第一次header数据
                    await forwarder.send_all(data)
                elif header.is_proxy2:
                    # 中转代理 => 代理 => 目标server
                    # conn = 中转代理
                    # forwarder = 目标server
                    forwarder: trio.SocketStream = await trio.open_tcp_stream(header.host, header.port)
                    data = b"HTTP/1.1 200 Connection Established\r\n\r\n"
                    # await conn.send_all(data)
                else:
                    # 客户端 => 代理 => 目标server
                    # conn = 源客户端
                    # forwarder = 目标server
                    # 需要先响应客户端建立ssl连接
                    data = b"HTTP/1.1 200 Connection Established\r\n\r\n"
                    await conn.send_all(data)
                    forwarder: trio.SocketStream = await trio.open_tcp_stream(header.host, header.port)
                # log.info(f'send: {data!r}')
                # 之后转发body的加密数据
                async with trio.open_nursery() as nursery:
                    nursery.start_soon(self.client2forwarder, conn, forwarder)
                    nursery.start_soon(self.forwarder2client, forwarder, conn)
            else:
                if header.proxy_host and header.proxy_port:
                    forwarder: trio.SocketStream = await trio.open_tcp_stream(header.proxy_host, header.proxy_port)
                    header.headers.pop('proxy')
                    data = [b'%s: %s' % (item[0], item[1]) for item in header.headers.raw]
                    data.insert(0, header.line0)
                    data = b'\r\n'.join(data)
                    data = b'%s\r\n\r\n' % data
                else:
                    forwarder: trio.SocketStream = await trio.open_tcp_stream(header.host, header.port)
                    data = header.data
                log.info(f'send: {data!r}')
                # 转发连接进来的第一次数据
                await forwarder.send_all(data)
                async with trio.open_nursery() as nursery:
                    # 转发后续传输的数据
                    nursery.start_soon(self.client2forwarder, conn, forwarder)
                    nursery.start_soon(self.forwarder2client, forwarder, conn)
                # async for data in forwarder:  # 这里如果是https请求，会一直循环在这等待接收数据
                #     # http响应的
                #     # b'HTTP/1.1 302 Moved Temporarily\r\nServer: AkamaiGHost\r\nContent-Length: 0\r\nLocation: https://steamcommunity.com/\r\nDate: Mon, 11 Apr 2022 07:34:27 GMT\r\nConnection: close\r\n\r\n'
                #     # 如果是https请求
                #     # 会响应密文, 服务端并没有通知客户端关闭连接
                #     await conn.send_all(data)  # 给客户端转发数据
            log.info(f"echo_server {ident}: connection closed")
            # FIXME: add discussion of MultiErrors to the tutorial, and use
            # MultiError.catch here. (Not important in this case, but important if the
            # server code uses nurseries internally.)
        except Exception as exc:
            # Unhandled exceptions will propagate into our parent and take
            # down the whole program. If the exception is KeyboardInterrupt,
            # that's what we want, but otherwise maybe not...
            log.info(f"echo_server {ident}: crashed: {exc!r}")

    async def __call__(self, *args, **kwargs):
        # pass
        await self.handle(*args, **kwargs)


async def main(port=12345, password=''):
    proxy = Proxy(password)
    log.info(f'Running on 127.0.0.1:{port}')
    await trio.serve_tcp(proxy, port, host='0.0.0.0')


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 2 else 12345
    if len(sys.argv) == 2:
        password = sys.argv[1]
        port = 5566
    else:
        port = 12345
        password = '000000'

    trio.run(main, port, password)
