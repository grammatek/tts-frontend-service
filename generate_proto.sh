#!/bin/sh

# Generates _pb2.py and _pb2_grpc.py for messages and services

# Make sure to have installed requirements before running this script

python3 -m grpc_tools.protoc -I./tts-frontend-proto/ --python_out=src/generated/ --grpc_python_out=src/generated/ tts-frontend-proto/services/text_preprocessing_service.proto
python3 -m grpc_tools.protoc -I./tts-frontend-proto/ --python_out=src/generated/ --grpc_python_out=src/generated/ tts-frontend-proto/messages/text_preprocessing_message.proto