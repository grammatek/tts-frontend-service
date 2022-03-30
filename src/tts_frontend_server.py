import sys
from os.path import dirname

from manager.tokens import TagToken, CleanToken, NormalizedToken, TranscribedToken

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

    def init_clean_token(self, token: CleanToken) -> msg.CleanToken:
        """

        """
        orig = token.original_token
        embedded_orig = msg.Token(name=orig.name, index=orig.token_index, span_from=orig.start, span_to=orig.end)
        clean_token = msg.CleanToken(original_token=embedded_orig, name=token.name, index=token.token_index)

        return clean_token

    def init_norm_token(self, token: NormalizedToken) -> msg.NormalizedToken:
        """

        """
        clean = token.clean_token
        orig = clean.original_token
        embedded_orig = msg.Token(name=orig.name, index=orig.token_index, span_from=orig.start, span_to=orig.end)
        embedded_clean = msg.CleanToken(original_token=embedded_orig, name=clean.name, index=clean.token_index)
        norm_token = msg.NormalizedToken(clean_token=embedded_clean, name=token.name, index=token.token_index)

        return norm_token

    def init_transcr_token(self, token: TranscribedToken) -> msg.TranscribedToken:
        """

        """
        norm = token.normalized
        clean = norm.clean_token
        orig = clean.original_token
        embedded_orig = msg.Token(name=orig.name, index=orig.token_index, span_from=orig.start, span_to=orig.end)
        embedded_clean = msg.CleanToken(original_token=embedded_orig, name=clean.name, index=clean.token_index)
        embedded_norm = msg.NormalizedToken(clean_token=embedded_clean, name=norm.name)
        transcribed = msg.TranscribedToken(normalized_token=embedded_norm, name=token.name)
        return transcribed

    def Clean(self, request: msg.TextCleanRequest, context) -> msg.TextCleanResponse:
        """Clean text, returns clean text without non-valid chars or symbols.
        """
        context.set_code(grpc.StatusCode.OK)

        cleanRes = self.manager.clean(request.content)
        response = msg.TextCleanResponse()
        for token in cleanRes:

            if isinstance(token, TagToken):
                tagTok = msg.TagToken(name=token.name, index=token.token_index)
                tok = msg.CleanTokenList(tag=tagTok)
            else:
                clean_token = self.init_clean_token(token)
                tok = msg.CleanTokenList(cleaned=clean_token)

            response.tokens.append(tok)

        return response

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

    def Preprocess(self, request: msg.PreprocessRequest, context) -> msg.PreprocessedResponse:
        """Preprocess text for TTS, including conversion to X-SAMPA
        """
        context.set_code(grpc.StatusCode.OK)
        if request.domain == msg.NORM_DOMAIN_SPORT:
            domain = 'sport'
        else:
            domain = ''
        transcribed_res = self.manager.transcribe(request.content, domain)
        response = msg.PreprocessedResponse()
        for token in transcribed_res:
            if isinstance(token, TagToken):
                tagTok = msg.TagToken(name=token.name, index=token.token_index)
                tok = msg.TranscribedTokenList(tag=tagTok)
            else:
                transcribed_token = self.init_transcr_token(token)
                tok = msg.TranscribedTokenList(transcribed=transcribed_token)

            response.tokens.append(tok)

        return response

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