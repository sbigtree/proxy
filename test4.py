import re
import _thread
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR


def getAddr(d):
    a = re.search("Host: (.*)\r\n", d)
    if a == None:
        a = re.search("Host: (.*)", d)
    host = a.group(1)
    a = host.split(":")
    if len(a) == 1:
        return (a[0], 80)
    else:
        return (a[0], int(a[1]))


def SendAndRecv(Stream, BuffList, i, j):
    while True:
        BuffList[i] = Stream[i].recv(1024)
        # print(i, "接收到:", BuffList[i])
        if BuffList[i] == b'':
            break
        Stream[j].send(BuffList[i])


def exit(serverIP, serverPort):
    while True:
        _str = input("输入q退出！！！")
        if _str == 'q':
            sock = socket(AF_INET, SOCK_STREAM)
            sock.connect((serverIP, serverPort))
            sock.send('exit'.encode())
            sock.close()
            break
    pass


def interBoth(tmp, client):
    Stream = [tmp, client]
    BufferList = [b'', b'']
    _thread.start_new_thread(
        SendAndRecv, (Stream, BufferList, 0, 1,))
    _thread.start_new_thread(
        SendAndRecv, (Stream, BufferList, 1, 0,))
    print("已创建线程！！！！！", BufferList)
    while BufferList[0] == b'' and BufferList[1] == b'':
        pass
    while BufferList[0] != b'' or BufferList[1] != b'':
        pass
    client.close()
    tmp.close()


# print(BufferList)


def process(request_data, tmp):
    Addr = getAddr(request_data)
    try:
        client = socket(AF_INET, SOCK_STREAM)
        try:
            client.connect(Addr)
        except:
            client.close()
        else:
            el = request_data.split("\r\n")
            if el[0].find('HTTP') != -1:
                part = el[0].split(' ')
                if part[0] == 'CONNECT':
                    response_start_line = "HTTP/1.1 200 Connection Established\r\n\r\n"
                    # response = "HTTP/1.1 407 Unauthorized\r\n"
                    tmp.send(response_start_line.encode())
                    interBoth(tmp, client)
                else:
                    # 此处为GET、POST请求方式实现
                    client.send(request_data)
                    interBoth(tmp, client)

    except Exception as identifier:
        print(identifier)

    pass


def local(serverIP, serverPort):
    tcpSocket = socket(AF_INET, SOCK_STREAM)
    tcpSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    tcpSocket.bind((serverIP, serverPort))
    tcpSocket.listen(5)
    while True:
        tmp, addr = tcpSocket.accept()
        msg = tmp.recv(1024)

        _thread.start_new_thread(process, (msg.decode(), tmp,))
    pass


if __name__ == "__main__":
    serverIP = '127.0.0.1'
    serverPort = 12345
    # _thread.start_new_thread(exit, (serverIP, serverPort,))
    local(serverIP, serverPort)

    pass

