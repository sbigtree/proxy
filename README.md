一个代理服务器


###下载
```shell
git clone https://github.com/sbigtree/proxy.git
```

### 启动

### 创建虚拟环境
```shell
mkdir ~/.venv
python3 -m venv ~/.venv/python3.9-proxy
```

```shell
# 进入虚拟环境
source ~/.venv/python3.9-proxy/bin/activate
# 安装依赖
pip install -r requirements.txt
# 前台启动
python  main.py
# 后台启动
python  main.py password >/dev/null 2>&1 &

```

### 测试

```shell
curl https://127.0.0.1:8443 -v -k --proxy admin:pass@127.0.0.1:12345
curl https://127.0.0.1:8443 -v -k --proxy admin:pass@127.0.0.1:3129

curl https://steamcommunity.com/ -v -k --proxy admin:pass@127.0.0.1:3127
curl https://steamcommunity.com/ -v -k --proxy admin:pass@127.0.0.1:5566
curl https://steamcommunity.com/ -v -k --proxy 000000:000000@127.0.0.1:12345
curl https://steamcommunity.com/ -v -k --proxy 000000:000000@127.0.0.1:3128
curl https://baidu.com.com/ -v -k --proxy 000000:000000@127.0.0.1:12345
```