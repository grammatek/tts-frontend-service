import sys
from os.path import dirname

import manager.tokens

sys.path.append(dirname(__file__)+'/generated/')

from concurrent import futures
import logging
import grpc

from generated.messages import text_preprocessing_message_pb2 as msg
from generated.services import text_preprocessing_service_pb2_grpc as service

from manager.textprocessing_manager import Manager


class TTSFrontendServicer(service.TextPreprocessingServicer):
    """Provides methods that implement functionality of tts frontend server."""

    def __init__(self):
        # init pipeline
        self.manager = Manager()

    def Normalize(self, request: msg.NormalizeRequest, context) -> msg.NormalizedResponse:
        """Normalize text for TTS, returns normalized text prepared for g2p
        """
        context.set_code(grpc.StatusCode.OK)
        if request.domain == msg.NORM_DOMAIN_SPORT:
            domain = 'sport'
        else:
            domain = ''
        normalized = self.manager.normalize(request.content, domain)
        response = msg.NormalizedResponse()
        for token in normalized:
            response.tokens.append(token)

        return response

    def TTSPreprocess(self, request, context):
        """Preprocess text for TTS, including conversion to X-SAMPA
        """
        context.set_code(grpc.StatusCode.NOT_IMPLEMENTED)

    def GetDefaultPhonemeDescription(self, request, context):
        """Default values for the phoneme description
        """
        context.set_code(grpc.StatusCode.NOT_IMPLEMENTED)

    def GetVersion(self, request, context):
        context.set_code(grpc.StatusCode.OK)
        return msg.AbiVersionResponse(version=msg.ABI_VERSION.ABI_VERSION_CURRENT)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service.add_TextPreprocessingServicer_to_server(TTSFrontendServicer(), server)
    server.add_insecure_port('[::]:8080')
    server.start()
    server.wait_for_termination()


if __name__=='__main__':
    logging.basicConfig()
    serve()