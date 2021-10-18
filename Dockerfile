
FROM ubuntu:18.04

LABEL maintainer="tomer.klein@gmail.com"
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8

RUN apt update -yqq

RUN apt -yqq install python3-pip
    
RUN  pip3 install --upgrade pip --no-cache-dir && \
     pip3 install --upgrade setuptools --no-cache-dir
     
RUN mkdir -p /opt/decompose
 
COPY decompose /opt/decompose
WORKDIR /opt/decompose/ 

RUN pip3 install -r requirements.txt

EXPOSE 8080

ENTRYPOINT ["/usr/bin/python3", "decompose.py"]
