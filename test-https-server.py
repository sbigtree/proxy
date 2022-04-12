#!/usr/bin/env python3

# To generate a certificate use:
# openssl req -newkey rsa:4096 -nodes -keyout key.pem -x509 -days 365 -out cert.pem

from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl

port = 8443
httpd = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
httpd.socket = ssl.wrap_socket(httpd.socket, keyfile='server.key', certfile="server.cert", server_side=True)

print("Server running on https://0.0.0.0:" + str(port))

httpd.serve_forever()