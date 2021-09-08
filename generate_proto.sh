#!/bin/sh

# Generates _pb2.py and _pb2_grpc.py for messages and services

python3 -m venv service-venv
source service-venv/bin/activate
GRPC_TOOLS_FOUND=`pip list | grep grpcio-tools`
if [ "$?" -ne 0  ]; then
	pip install grpcio-tools
fi

python3 -m grpc_tools.protoc -I./proto/ --python_out=src/generated/ --grpc_python_out=src/generated/ proto/services/tts_frontend_service.proto
python3 -m grpc_tools.protoc -I./proto/ --python_out=src/generated/ --grpc_python_out=src/generated/ proto/messages/tts_frontend_message.proto