FROM 192.168.10.10/hypermotion/base:latest

MAINTAINER Chen Chunzai <chenchunzai@oneprocloud.com>

COPY ./etc/pip/ /root/.pip/
COPY ./tools/wmi-1.3.14-4.el7.art.x86_64.rpm /tmp
COPY ./etc/repo/hypermotion.repo /etc/yum.repos.d/hypermotion.repo
COPY ./ /opt/prophet

# Install prophet
RUN pip install -e /opt/prophet && yum install -y nmap && yum install -y /tmp/wmi-1.3.14-4.el7.art.x86_64.rpm
