FROM 192.168.10.10/hypermotion/base:latest

MAINTAINER Chen Chunzai <chenchunzai@oneprocloud.com>

COPY ./etc/pip/ /root/.pip/
COPY ./etc/repo/hypermotion.repo /etc/yum.repos.d/hypermotion.repo
COPY ./ /opt/prophet

# Install prophet
RUN pip install -e /opt/prophet && yum install -y nmap
