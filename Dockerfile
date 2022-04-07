# syntax=docker/dockerfile:1
FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED=1
ENV TTS_FRONTEND=/tts_frontend_service

RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools
RUN apt-get update && apt-get install -y git

WORKDIR $TTS_FRONTEND

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Install OpenJDK-11
RUN apt-get update && \
    apt-get install -y openjdk-11-jdk && \
    apt-get install -y ant && \
    apt-get install ca-certificates-java && \
    apt-get clean; \
    update-ca-certificates -f;

# Setup JAVA_HOME
ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64/
RUN export JAVA_HOME

COPY . $TTS_FRONTEND
RUN cd $TTS_FRONTEND && ./generate_proto.sh

EXPOSE 8080
CMD ["./run.sh"]