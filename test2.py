import os
import socket
import ssl
import sys

hostname = 'www.python.org'
hostname = 'wx.ccmo.cc'
hostname = '207.246.110.136'
hostname = '127.0.0.1'
# PROTOCOL_TLS_CLIENT requires valid cert chain and hostname
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
path = os.path.join(os.getcwd(),'proxy.cert')
path = os.path.join(os.getcwd(),'proxy.cert')
# context.load_verify_locations('stunnel.pem')
context.load_verify_locations('proxy.cert')
# context = ssl.create_default_context()

# with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
#     with context.wrap_socket(sock, server_hostname=hostname) as ssock:
#         print(ssock.version())

with socket.create_connection((hostname, 8443)) as sock:
    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
        print(ssock.version())
        ssock.send(b'222')
    ssock.close()