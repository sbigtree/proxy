### 生成证书

```shell
openssl req -new -x509 -days 365 -nodes -out proxy.cert -keyout proxy.key
```

### 注意：生成私钥，需要提供一个至少4位的密码

```shell
openssl genrsa -des3 -out server.key 2048
```

### 生成CSR（证书签名请求）

```shell

openssl req -new -key server.key -out server.csr
```

### 删除私钥中的密码

```shell

openssl rsa -in server.key -out server.key
```

### 生成自签名证书

```shell

openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.cert
```

### key crt合成一个文件

```shell

cat server.key server.cert > server.pem
```

#### 创建虚拟环境

```sh
python -m venv ~/.venv/python3.9-proxy
source ~/.venv/python3.9-proxy/bin/activate
```

#### 导出依赖包

```sh
pip freeze > requirements.txt
```

#### 安装

```shell
pip install -r requirements.txt
```

### 启动

```shell
# 进入虚拟环境
source ~/.venv/python3.9-proxy/bin/activate
# 后台启动
python  main.py >/dev/null 2>&1 &
# 前台启动
python  main.py
```

### 测试

```shell
curl https://127.0.0.1:8443 -v -k --proxy admin:qy83346348@127.0.0.1:12345
curl https://127.0.0.1:8443 -v -k --proxy admin:qy83346348@127.0.0.1:3129
```