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

ENV GOOGLEAPIS_DIR=/app/googleapis
RUN git clone --depth 1 https://github.com/googleapis/googleapis ${GOOGLEAPIS_DIR}

RUN curl -L https://github.com/grammatek/tts-frontend-proto/archive/bc6b4a3c8abd96f8ba65db94118a676016a4a7ea.tar.gz | tar zxvf - \
    && mv tts-frontend-proto-bc6b4a3c8abd96f8ba65db94118a676016a4a7ea/messages $TTS_FRONTEND/ \
    && mv tts-frontend-proto-bc6b4a3c8abd96f8ba65db94118a676016a4a7ea/services $TTS_FRONTEND/ \
    && rm -rf tts-frontend-proto-bc6b4a3c8abd96f8ba65db94118a676016a4a7ea

RUN mkdir -p $TTS_FRONTEND/src/generated/

COPY googleapis/ $TTS_FRONTEND/googleapis

COPY . $TTS_FRONTEND
RUN python3 -m grpc_tools.protoc -I./googleapis -I. --python_out=$TTS_FRONTEND/src/generated/ --grpc_python_out=$TTS_FRONTEND/src/generated/ services/preprocessing_service.proto
RUN python3 -m grpc_tools.protoc -I./googleapis -I. --python_out=$TTS_FRONTEND/src/generated/ --grpc_python_out=$TTS_FRONTEND/src/generated/ messages/preprocessing_message.proto
# Needed as dependency for service reflection
RUN python3 -m grpc_tools.protoc -I./googleapis -I. --python_out=$TTS_FRONTEND/src/generated/ \
        --grpc_python_out=$TTS_FRONTEND/src/generated/ ./googleapis/google/api/annotations.proto ./googleapis/google/api/http.proto

RUN rm -rf $TTS_FRONTEND/tts-frontend-proto/

EXPOSE 8080
CMD ["./run.sh"]