import sys
from os.path import dirname
sys.path.append(dirname(__file__)+'/generated/')

from concurrent import futures
import logging
import grpc
from generated.messages import tts_frontend_message_pb2
from generated.services import tts_frontend_service_pb2_grpc


class TTSFrontendServicer(tts_frontend_service_pb2_grpc.TTSFrontendServicer):
    """Provides methods that implement functionality of tts frontend server."""

    def __init__(self):
        # init normalizer
        return

    def Normalize(self, request, context):
        """Normalize text for TTS, returns normalized text prepared for g2p
        """
        context.set_code(grpc.StatusCode.OK)

    def TTSPreprocess(self, request, context):
        """Preprocess text for TTS, including conversion to X-SAMPA
        """
        context.set_code(grpc.StatusCode.OK)

    def GetDefaultPhonemeDescription(self, request, context):
        """Default values for the phoneme description
        """
        context.set_code(grpc.StatusCode.OK)

    def GetVersion(self, request, context):
        context.set_code(grpc.StatusCode.OK)
        return tts_frontend_message_pb2.AbiVersionResponse(version=tts_frontend_message_pb2.ABI_VERSION.ABI_VERSION_CURRENT)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tts_frontend_service_pb2_grpc.add_TTSFrontendServicer_to_server(TTSFrontendServicer(), server)
    server.add_insecure_port('[::]:8080')
    server.start()
    server.wait_for_termination()


if __name__=='__main__':
    logging.basicConfig()
    serve()