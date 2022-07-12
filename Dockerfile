# syntax=docker/dockerfile:1
FROM python:3.9-slim-buster

ENV PYTHONUNBUFFERED=1
ENV TTS_FRONTEND=/tts_frontend_service

RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools
RUN apt-get update && apt-get install -y git gcc g++

WORKDIR $TTS_FRONTEND

COPY requirements.txt requirements.txt
#RUN pip3 install --upgrade pip # use 21.3.1 for Fairseq
RUN pip3 install pip==21.3.1
#RUN pip3 install editdistance not needed?
RUN pip3 install -r requirements.txt --force-reinstall

RUN apt-get update -yqq && \
    apt-get install -y curl git

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

RUN git clone --depth 1 https://github.com/googleapis/googleapis

RUN curl -L https://github.com/grammatek/tts-frontend-proto/archive/f5a6554026dfa84eb13a57538f820900b4215242.tar.gz | tar zxvf - \
    && mv tts-frontend-proto-f5a6554026dfa84eb13a57538f820900b4215242/messages $TTS_FRONTEND/ \
    && mv tts-frontend-proto-f5a6554026dfa84eb13a57538f820900b4215242/services $TTS_FRONTEND/ \
    && rm -rf tts-frontend-proto-f5a6554026dfa84eb13a57538f820900b4215242

RUN mkdir -p $TTS_FRONTEND/src/generated/

COPY . $TTS_FRONTEND
RUN python3 -m grpc_tools.protoc -I./googleapis -I. --python_out=$TTS_FRONTEND/src/generated/ --grpc_python_out=$TTS_FRONTEND/src/generated/ services/preprocessing_service.proto
RUN python3 -m grpc_tools.protoc -I./googleapis -I. --python_out=$TTS_FRONTEND/src/generated/ --grpc_python_out=$TTS_FRONTEND/src/generated/ messages/preprocessing_message.proto
# Needed as dependency for service reflection
RUN python3 -m grpc_tools.protoc -I./googleapis -I. --python_out=$TTS_FRONTEND/src/generated/ \
        --grpc_python_out=$TTS_FRONTEND/src/generated/ ./googleapis/google/api/annotations.proto ./googleapis/google/api/http.proto

RUN rm -rf $TTS_FRONTEND/tts-frontend-proto/

EXPOSE 8080
CMD ["./run.sh"]