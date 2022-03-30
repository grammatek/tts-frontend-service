import sys
from os.path import dirname

from manager.tokens import TagToken, NormalizedToken

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

    def init_norm_token(self, token: NormalizedToken) -> msg.NormalizedToken:
        """
        CleanToken clean_token = 1;
  string name = 2; // the normalized version of the token
  int32 index = 3;
  NormalizationDomain domain = 4;
        """
        clean = token.clean_token
        orig = clean.original_token
        embedded_orig = msg.Token(name=orig.name, index=orig.token_index, span_from=orig.start, span_to=orig.end)
        embedded_clean = msg.CleanToken(original_token=embedded_orig, name=clean.name, index=clean.token_index)
        norm_token = msg.NormalizedToken(clean_token=embedded_clean, name=token.name, index=token.token_index)

        return norm_token

    def Normalize(self, request: msg.NormalizeRequest, context) -> msg.NormalizedResponse:
        """Normalize text for TTS, returns normalized text prepared for g2p
        """
        context.set_code(grpc.StatusCode.OK)
        if request.domain == msg.NORM_DOMAIN_SPORT:
            domain = 'sport'
        else:
            domain = ''
        normalizedRes = self.manager.normalize(request.content, domain)
        response = msg.NormalizedResponse()
        for token in normalizedRes:

            if isinstance(token, TagToken):
                tagTok = msg.TagToken(name=token.name, index=token.token_index)
                tok = msg.NormalizedTokenList(tag=tagTok)
            else:
                norm_token = self.init_norm_token(token)
                tok = msg.NormalizedTokenList(normalized=norm_token)

            response.tokens.append(tok)

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