import httpx

# 3129 => 34567 => 12345 => 3344 => 目标host
#   \                /       \        /
#        stunnel               proxy
proxies = httpx.Proxy(url='http://127.0.0.1:3127', auth=('000000', '000000'), headers={
    # 'proxy': '127.0.0.1:5566'
})
proxies1 = httpx.Proxy(url='http://127.0.0.1:3127', auth=('nihao', 'nihao'), headers={
    'proxy': '207.246.73.116:5566'
})
proxies2 = httpx.Proxy(url='http://127.0.0.1:12345', auth=('nihao', 'nihao'), headers={
    'proxy': '127.0.0.1:5566'
})

# res = httpx.Client(proxies={'https': 'http://127.0.0.1:12345'}).get('http:///127.0.0.1:8443')
# res = httpx.Client(proxies={'https': 'http://127.0.0.1:12345'}).get('https://blog.csdn.net/')
# session = httpx.Client(http2=False, headers=None, verify=False,proxies={'https://': 'http://127.0.0.1:12345'})
# session = httpx.Client(http2=False, headers=None, verify=False,proxies=proxies)
session = httpx.Client(http2=False, headers=None, verify=False,proxies=proxies2)
# session = httpx.Client(http2=False, headers=None, verify=False,proxies=proxies2)
# session = httpx.Client(http2=False, headers=None, verify=False,proxies={'https://':'http://127.0.0.1:3344'})
res = session.get(url='https://127.0.0.1:8443/test/test')
# res = session.get(url='https://steamcommunity.com')
# res = session.get(url='http://127.0.0.1:8060/test/test')
headers = session.headers
print(res.text)
pass