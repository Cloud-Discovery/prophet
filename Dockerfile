FROM centos:7

MAINTAINER Ray Sun <ray.sun@oneprocloud.com>

ENV LANG en_US.UTF-8

COPY ./ /opt/prophet
WORKDIR /opt/prophet

RUN mv /opt/prophet/etc/pip /root/.pip && \
    yum -y install epel-release && \
    yum clean all && yum makecache && \
    yum -y install gcc python2-pip python-devel python-pbr && \
    pip install pip==9.0.3 && \
    yum install -y nmap && \
    yum install -y /opt/prophet/tools/wmi-1.3.14-4.el7.art.x86_64.rpm && \
    pip install -e /opt/prophet
