#!/bin/sh

# Generates _pb2.py and _pb2_grpc.py for messages and services

# Make sure to have installed requirements before running this script

# clone the google apis
GOOGLEAPIS_DIR=googleapis/
if [ ! -d ${GOOGLEAPIS_DIR} ]; then
  git clone --depth 1 https://github.com/googleapis/googleapis ${GOOGLEAPIS_DIR}
fi

python3 -m grpc_tools.protoc -I./googleapis -I./tts-frontend-proto/ --python_out=src/generated/ \
        --grpc_python_out=src/generated/ tts-frontend-proto/services/preprocessing_service.proto
python3 -m grpc_tools.protoc -I./googleapis -I./tts-frontend-proto/ --python_out=src/generated/ \
        --grpc_python_out=src/generated/ tts-frontend-proto/messages/preprocessing_message.proto