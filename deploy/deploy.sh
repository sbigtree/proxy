#!/bin/bash
WORK_DIR=$(pwd)
PYTHON_VERSION='Python-3.9.0.tgz'
timedatectl # 查看时区
timedatectl set-timezone Asia/Shanghai  # 设置时区
timedatectl set-ntp true # 同步时间到ntp

yum update -y
yum -y install vim net-tools lsof wget gcc make libffi-devel zlib-devel readline-devel bzip2-devel ncurses-devel sqlite-devel gdbm-devel xz-devel tk-devel openssl-devel


### python3.9
if [ $(type python3.9 >/dev/null 2>&1) $? -eq 0 ];then
  echo -e "\033[42m[python3.9 已经安装了]\033[0m"
else
  echo -e "\033[42m[正在安装 python3.9]\033[0m"
  cd $WORK_DIR
  yum install libffi-devel gcc -y
  tar -zxvf $PYTHON_VERSION
  cd Python-3.9.0
  ./configure
  make clean && make && make install
  if [ $? -ne 0 ];then
    echo -e "\033[1;31m[安装 python3.9 失败]\033[0m"
    exit 1
  fi
  ln -s -f /usr/local/bin/python3.9 /usr/local/bin/python
  mkdir ~/.venv
  python3 -m venv ~/.venv/python3.9-proxy
  source /root/.venv/python3.9-proxy/bin/activate

fi



### zsh
cd $WORK_DIR
echo -e "\033[42m[正在安装 ohmyzsh]\033[0m"
yum -y install zsh
chmod +x ./ohmyzsh.sh
./ohmyzsh.sh

iptables -F # 删除所有规则