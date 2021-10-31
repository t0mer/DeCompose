
FROM techblog/fastapi:latest

LABEL maintainer="tomer.klein@gmail.com"
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8

RUN mkdir -p /opt/decompose
 
COPY decompose /opt/decompose
WORKDIR /opt/decompose/ 

RUN pip3 install -r requirements.txt

EXPOSE 8080

ENTRYPOINT ["/usr/bin/python3", "decompose.py"]
