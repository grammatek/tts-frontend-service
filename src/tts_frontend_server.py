import sys
from os.path import dirname
sys.path.append(dirname(__file__)+'/generated/')

from concurrent import futures
import logging
import grpc

from regina_normalizer.main import Normalizer
from generated.messages import tts_frontend_message_pb2
from generated.services import tts_frontend_service_pb2_grpc


class TTSFrontendServicer(tts_frontend_service_pb2_grpc.TTSFrontendServicer):
    """Provides methods that implement functionality of tts frontend server."""

    def __init__(self):
        # init normalizer
        self.normalizer = Normalizer()
        return

    def init_tokenbased_response(self, normalized_arr):
        response = tts_frontend_message_pb2.TokenBasedNormalizedResponse()
        for sentence in normalized_arr:
            sentence_response = tts_frontend_message_pb2.TokenBasedNormalizedSentence()
            norm_sent = ''
            for ind, pair in enumerate(sentence):
                info = tts_frontend_message_pb2.RawNormalizedTokenInfo()
                info.original_token = pair[0]
                info.normalized_token = pair[1]
                info.original_index = ind
                if info.original_token != info.normalized_token:
                    info.has_changed = True
                sentence_response.token_info.append(info)
                norm_sent += info.normalized_token + ' '
            sentence_response.normalized_sentence = norm_sent.strip()
            response.sentence.append(sentence_response)

        return response

    def Normalize(self, request, context):
        """Normalize text for TTS, returns normalized text prepared for g2p
        """
        context.set_code(grpc.StatusCode.OK)
        if request.domain == tts_frontend_message_pb2.NORM_DOMAIN_SPORT:
            domain = 'sport'
        else:
            domain = ''
        normalized = self.normalizer.normalize(request.content, domain)
        response = tts_frontend_message_pb2.NormalizeResponse()
        for sentence in normalized:
            response.normalized_sentence.append(sentence[0])

        return response

    def NormalizeTokenwise(self, request, context):
        """Normalize text for TTS, returns normalized text prepared for g2p
        """
        context.set_code(grpc.StatusCode.OK)
        if request.domain == tts_frontend_message_pb2.NORM_DOMAIN_SPORT:
            domain = 'sport'
        else:
            domain = ''
        normalized = self.normalizer.normalize_tokenwise(request.content, domain)
        response = self.init_tokenbased_response(normalized)

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