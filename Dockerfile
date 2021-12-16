FROM centos:7

MAINTAINER Ray Sun <ray.sun@oneprocloud.com>

ENV LANG en_US.UTF-8

COPY ./ /opt/prophet
WORKDIR /opt/prophet

RUN mv /opt/prophet/etc/pip /root/.pip && \
    yum -y install epel-release && \
    yum clean all && yum makecache && \
    yum -y install gcc sshpass && \
    yum -y install python3 python3-pip python36-devel python36-devel python36-pbr python36-setuptools && \
    yum install -y nmap && \
    yum install -y /opt/prophet/tools/wmi-1.3.14-4.el7.art.x86_64.rpm && \
    pip3 install -U pip && \
    pip3 install -e /opt/prophet

COPY ./tools/entrypoints.sh /entrypoint.sh
RUN chmod a+x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
