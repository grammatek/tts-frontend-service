import sys
from os.path import dirname

from manager.tokens import TagToken, CleanToken, NormalizedToken, TranscribedToken

sys.path.append(dirname(__file__)+'/generated/')

from concurrent import futures
import logging
import grpc
from google.protobuf import empty_pb2

from generated.messages import preprocessing_message_pb2 as msg
from generated.services import preprocessing_service_pb2_grpc as service

from manager.textprocessing_manager import Manager


class TTSFrontendServicer(service.PreprocessingServicer):
    """Provides methods that implement functionality of a TTS frontend pipeline.
    For example usage see `tts_frontend_client_example.py` """

    def __init__(self):
        # init pipeline
        self.manager = Manager()

    @staticmethod
    def init_clean_token(token: CleanToken) -> msg.CleanToken:
        """
        Initialize a cleanToken message from the cleanToken object parameter.
        """
        orig = token.original_token
        embedded_orig = msg.Token(name=orig.name, index=orig.token_index, span_from=orig.start, span_to=orig.end)
        clean_token = msg.CleanToken(original_token=embedded_orig, name=token.name, index=token.token_index)

        return clean_token

    @staticmethod
    def init_norm_token(token: NormalizedToken) -> msg.NormalizedToken:
        """
        Initialize a normalizedToken message from the normalizedToken object parameter.
        """
        clean = token.clean_token
        orig = clean.original_token
        embedded_orig = msg.Token(name=orig.name, index=orig.token_index, span_from=orig.start, span_to=orig.end)
        embedded_clean = msg.CleanToken(original_token=embedded_orig, name=clean.name, index=clean.token_index)
        norm_token = msg.NormalizedToken(clean_token=embedded_clean, name=token.name, index=token.token_index)

        return norm_token

    @staticmethod
    def init_transcr_token(token: TranscribedToken) -> msg.TranscribedToken:
        """
        Initialize a transcribedToken message from the transcribedToken object parameter.
        A transcribedToken contains three embedded tokens: the original input token, the clean token,
        the normalized token, and finally the transcribed token. The original, clean and normalized tokens
        might be all identical (e.g. 'halló', 'halló', 'halló') but the transcribed token is represented in
        a phonetic alphabet (e.g. 'h a l ou').
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
        Status: the only parameter reachable form here is the parse_html, i.e. if request.parse_html == True
        the input string (request.content) will be processed as html with text extracted, english labels
        substituted by SSML-lang tags and HTML-tags either replaced by a dot or deleted.
        TODO: add other parameters of the text cleaner to the interface
        """
        context.set_code(grpc.StatusCode.OK)

        clean_result = self.manager.clean(request.content, html=request.parse_html)
        response = msg.TextCleanResponse()
        for token in clean_result:

            if isinstance(token, TagToken):
                tag_tok = msg.TagToken(name=token.name, index=token.token_index)
                tok = msg.CleanTokenList(tag=tag_tok)
            else:
                clean_token = self.init_clean_token(token)
                tok = msg.CleanTokenList(cleaned=clean_token)

            response.processed_content += token.name + ' '
            response.tokens.append(tok)

        return response

    def Normalize(self, request: msg.NormalizeRequest, context) -> msg.NormalizedResponse:
        """Normalize text for TTS, returns normalized text prepared for g2p.
        Accessible parameter is the normalization domain which can be set to msg.NORM_DOMAIN_SPORT if the
        input text is known to have sport as subject. Causes '2-1' to be normalized to 'tvö <sil> eitt' instead of
        'tvö til eitt' as in the default domain setting.
        """
        context.set_code(grpc.StatusCode.OK)
        if request.domain == msg.NORM_DOMAIN_SPORT:
            domain = 'sport'
        else:
            domain = ''
        normalized_result = self.manager.normalize(request.content, domain)
        response = msg.NormalizedResponse()
        for token in normalized_result:

            if isinstance(token, TagToken):
                tag_token = msg.TagToken(name=token.name, index=token.token_index)
                tok = msg.NormalizedTokenList(tag=tag_token)
            else:
                norm_token = self.init_norm_token(token)
                tok = msg.NormalizedTokenList(normalized=norm_token)

            response.tokens.append(tok)
            # don't add a tagToken's name to processed content string if the user doesn't want tags in the result string
            if isinstance(token, TagToken) and request.no_tag_tokens_in_content:
                continue
            response.processed_content += token.name + ' '

        return response

    def Preprocess(self, request: msg.PreprocessRequest, context) -> msg.PreprocessedResponse:
        """Preprocess text for TTS, including conversion to X-SAMPA. Same settings for cleaning and normalizing
        apply as described in Clean() and Normalize(), and additionally the following parameters can be
        set:
        """
        context.set_code(grpc.StatusCode.OK)
        if request.domain == msg.NORM_DOMAIN_SPORT:
            domain = 'sport'
        else:
            domain = ''

        # add user dictionary, if present
        self.manager.set_g2p_custom_dict(request.pronunciation_dict)
        # add g2p settings, if present
        self.manager.set_g2p_syllab_symbol(request.description.syllabified)
        self.manager.set_g2p_word_separator(request.description.word_separator)
        self.manager.set_g2p_stress(request.description.stress_labels)
        # process the request
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

            # don't add a tagToken's name to processed content string if the user doesn't want tags in the result string
            if isinstance(token, TagToken) and request.no_tag_tokens_in_content:
                continue

            if request.description.word_separator:
                response.processed_content += token.name + f' {request.description.word_separator} '
            else:
                response.processed_content += token.name + ' '

        return response

    def GetDefaultParameters(self, request, context) -> msg.DefaultProcessingResponse:
        context.set_code(grpc.StatusCode.OK)
        return msg.DefaultProcessingResponse

    def GetVersion(self, request, context):
        context.set_code(grpc.StatusCode.OK)
        return msg.AbiVersionResponse(version=msg.ABI_VERSION.ABI_VERSION_CURRENT)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service.add_PreprocessingServicer_to_server(TTSFrontendServicer(), server)
    server.add_insecure_port('[::]:8080')
    server.start()
    server.wait_for_termination()


if __name__=='__main__':
    logging.basicConfig()
    serve()