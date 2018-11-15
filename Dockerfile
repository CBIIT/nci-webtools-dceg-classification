FROM centos:latest

RUN yum -y update \
 && yum -y install epel-release \
 && yum -y install \
    ant \
    gcc \
    httpd \
    httpd-devel \
    java-1.8.0-openjdk \
    python-devel \
    python-pip \
    R-core

RUN pip install --upgrade pip \
 && pip install \
    flask \
    mod_wsgi \
    stompest \
    stompest.async

RUN mkdir -p /deploy/app

WORKDIR /deploy/app