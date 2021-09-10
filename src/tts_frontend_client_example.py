import sys
from os.path import dirname

sys.path.append(dirname(__file__)+'/generated/')

import logging
import grpc
from google.protobuf import empty_pb2
from generated.services import tts_frontend_service_pb2_grpc
from generated.messages import tts_frontend_message_pb2 as msg_pb2


def get_version(stub):
    response = stub.GetVersion(empty_pb2.Empty())
    print(response)

def get_normalized_text(stub):
    message = msg_pb2.NormalizeRequest(content='voru 55 km eftir', domain=msg_pb2.NORM_DOMAIN_SPORT)
    response = stub.Normalize(message)
    print(response)

def get_tokenwise_normalized_text(stub):
    message = msg_pb2.NormalizeRequest(content='voru 55 km eftir. Enginn gat farið meira en 2 m.', domain=msg_pb2.NORM_DOMAIN_SPORT)
    response = stub.NormalizeTokenwise(message)
    print(response)


def run():
    with grpc.insecure_channel('localhost:8080') as channel:
        stub = tts_frontend_service_pb2_grpc.TTSFrontendStub(channel)
        print("-------------- GetVersion --------------")
        get_version(stub)
        print("-------------- Normalize --------------")
        get_normalized_text(stub)
        print("-------------- Normalize tokenwise --------------")
        get_tokenwise_normalized_text(stub)


if __name__=='__main__':
    logging.basicConfig()
    run()