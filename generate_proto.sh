#!/bin/sh

# Generates _pb2.py and _pb2_grpc.py for messages and services

# if venv does not yet exist, uncomment:
#python3 -m venv service-venv

source service-venv/bin/activate
GRPC_TOOLS_FOUND=`pip list | grep grpcio-tools`
if [ "$?" -ne 0  ]; then
	pip install grpcio-tools
fi

python3 -m grpc_tools.protoc -I./tts-frontend-proto/ --python_out=src/generated/ --grpc_python_out=src/generated/ tts-frontend-proto/services/text_preprocessing_service.proto
python3 -m grpc_tools.protoc -I./tts-frontend-proto/ --python_out=src/generated/ --grpc_python_out=src/generated/ tts-frontend-proto/messages/text_preprocessing_message.proto