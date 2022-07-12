import sys
from os.path import dirname
from concurrent import futures
from typing import Union
import logging

from manager.tokens import TagToken, Token
from manager.textprocessing_manager import Manager

sys.path.append(dirname(__file__)+'/generated/')
sys.path.append(dirname(__file__)+'/../googleapis/')

import grpc
from grpc_reflection.v1alpha import reflection

from generated.messages import preprocessing_message_pb2 as msg
from generated.services import preprocessing_service_pb2
from generated.services import preprocessing_service_pb2_grpc as service

#TODO: create an accessor in tts-frontend to ensure sentence split tags are identical
SENTENCE_SPLIT = '<sentence>'


class TTSFrontendServicer(service.PreprocessingServicer):
    """Provides methods that implement functionality of a TTS frontend pipeline.
    For example usage see `tts_frontend_client_example.py` """

    def __init__(self):
        """
        Initialize the pipeline.
        """
        self.manager = Manager()

    @staticmethod
    def add_content(name: str,
                    request: Union[msg.TextCleanRequest, msg.NormalizeRequest, msg.PreprocessRequest]) -> str:
        """
        Compose the string to add to a content string, using word_separator if given. Return the string.
        """
        result_str = ''
        if hasattr(request, 'description'):
            if request.description.word_separator:
                result_str = name + f' {request.description.word_separator} '
        if not result_str:
            result_str = name + ' '

        return result_str

    def init_clean_token(self, token: Token) -> msg.Token:
        """
        Initialize a cleanToken message from the cleanToken object parameter.
        """
        return msg.Token(name=token.name, clean=token.clean, index=token.token_index, span_from=token.start,
                                  span_to=token.end)

    def init_norm_token(self, token: Token) -> msg.Token:
        """
        Initialize a normalizedToken message from the token object parameter.
        """
        clean = self.init_clean_token(token)
        for norm in token.normalized:
            norm_token = msg.NormalizedToken(normalized_string=norm.norm_str, pos=norm.pos,
                                             is_spellcorrected=norm.is_spellcorrected)
            clean.normalized.append(norm_token)

        return clean

    def init_transcr_token(self, token: Token) -> msg.Token:
        """
        Initialize a transcribedToken message from the transcribedToken object parameter.
        A transcribedToken contains three embedded tokens: the original input token, the clean token,
        the normalized token, and finally the transcribed token. The original, clean and normalized tokens
        might be all identical (e.g. 'halló', 'halló', 'halló') but the transcribed token is represented in
        a phonetic alphabet (e.g. 'h a l ou').
        """
        normalized = self.init_norm_token(token)
        for transcr in token.transcribed:
            transcribed = msg.TranscribedToken(name=transcr)
            normalized.transcribed.append(transcribed)
        return normalized

    def set_manager_params(self, request: msg.PreprocessRequest):
        # add user dictionary, if present
        self.manager.set_g2p_custom_dict(request.pronunciation_dict)
        # add g2p settings, if present
        self.manager.set_g2p_syllab_symbol(request.description.syllabified)
        self.manager.set_g2p_word_separator(request.description.word_separator)
        self.manager.set_g2p_stress(request.description.stress_labels)

    def get_domain(self, request: Union[msg.NormalizeRequest, msg.PreprocessRequest]) -> str:
        # TODO: add domain param in manager methods
        domain = ''
        if isinstance(request, msg.NormalizeRequest):
            domain = request.domain
        elif isinstance(request, msg.PreprocessRequest):
            domain = request.norm_request.domain

        if domain == msg.NORM_DOMAIN_SPORT:
            return 'sport'

        return domain

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
                tok = msg.TokenList(tag=tag_tok)
                response.processed_content += token.name + ' '
            else:
                clean_token = self.init_clean_token(token)
                tok = msg.TokenList(token=clean_token)
                response.processed_content += token.clean + ' '

            response.tokens.append(tok)

        return response

    def Normalize(self, request: msg.NormalizeRequest, context) -> msg.NormalizedResponse:
        """Normalize text for TTS, returns normalized text prepared for g2p.
        Accessible parameter is the normalization domain which can be set to msg.NORM_DOMAIN_SPORT if the
        input text is known to have sport as subject. Causes '2-1' to be normalized to 'tvö <sil> eitt' instead of
        'tvö til eitt' as in the default domain setting.
        """
        context.set_code(grpc.StatusCode.OK)
        domain = self.get_domain(request)

        normalized_result = self.manager.normalize(request.content, html=request.parse_html, split_sent=True)
        for elem in normalized_result:
            print(elem.to_json())
        response = msg.NormalizedResponse()
        curr_sent = ''
        # Assemble the response message from the normalizer results
        for token in normalized_result:
            if isinstance(token, TagToken):
                tag_token = msg.TagToken(name=token.name, index=token.token_index)
                tok = msg.TokenList(tag=tag_token)
                if token.name.strip() == SENTENCE_SPLIT:
                    response.processed_content.append(curr_sent.strip())
                    curr_sent = ''
                elif not request.no_tag_tokens_in_content:
                    curr_sent += self.add_content(token.name, request)
            else:
                norm_token = self.init_norm_token(token)
                tok = msg.TokenList(token=norm_token)
                for norm in token.normalized:
                    curr_sent += self.add_content(norm.norm_str, request)

            response.tokens.append(tok)

        if curr_sent:
            response.processed_content.append(curr_sent)

        return response

    def Preprocess(self, request: msg.PreprocessRequest, context) -> msg.PreprocessedResponse:
        """
        Preprocess text for TTS, including conversion to X-SAMPA.
        """
        context.set_code(grpc.StatusCode.OK)

        domain = self.get_domain(request)
        self.set_manager_params(request)
        # process the request
        transcribed_res = self.manager.transcribe(request.content, html=request.parse_html)
        response = msg.PreprocessedResponse()
        # a single response sentence
        curr_sent = ''
        # Assemble the response from the transcribed_res, both the response token list as well as the
        # response processed content (the list of sentence strings)
        for token in transcribed_res:
            print(token)
            if isinstance(token, TagToken):
                tag_tok = msg.TagToken(name=token.name, index=token.token_index)
                tok = msg.TokenList(tag=tag_tok)
                if token.name == SENTENCE_SPLIT:
                    response.processed_content.append(curr_sent.strip())
                    curr_sent = ''
                elif not request.no_tag_tokens_in_content:
                    curr_sent += self.add_content(token.name, request)
                response.tokens.append(tok)
            elif isinstance(token, Token):
                transcribed_token = self.init_transcr_token(token)
                tok = msg.TokenList(token=transcribed_token)
                curr_sent += self.add_content(' '.join(token.transcribed), request)
                response.tokens.append(tok)

        if curr_sent:
            response.processed_content.append(curr_sent)

        return response

    def GetDefaultParameters(self, request, context) -> msg.DefaultProcessingResponse:
        """ Return the default parameters for text cleaning, normalization and phoneme description.
        We only set the defined default values, proto default values like False for booleans, empty
        for lists, sets and strings, zero for ints, do not need to be explicitly set here.
        """
        context.set_code(grpc.StatusCode.OK)

        emoji_repl = msg.EmojiReplacement()
        emoji_repl.replacement = '.'
        text_cleaner_params = msg.TextCleanerParams(emoji_replacement=emoji_repl)

        norm_domain = msg.NormalizationDomain(norm_domain=msg.NORM_DOMAIN_OTHER)

        norm_params = msg.NormalizeRequest(cleaner_params=text_cleaner_params, domain=norm_domain, language_code='is-IS')

        phoneme_descr = msg.PhonemeDescription(alphabet=msg.PHONETIC_ALPHABET_SAMPA, format=msg.PHONEME_PLAIN,
                                               dialect=msg.DIALECT_STANDARD, model=msg.MODEL_LSTM)

        default_param_response = msg.DefaultProcessingResponse(normalization_params=norm_params,
                                                               phoneme_description=phoneme_descr)

        return default_param_response

    def GetVersion(self, request, context):
        context.set_code(grpc.StatusCode.OK)
        return msg.AbiVersionResponse(version=msg.ABI_VERSION.ABI_VERSION_CURRENT)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service.add_PreprocessingServicer_to_server(TTSFrontendServicer(), server)
    SERVICE_NAMES = (
        preprocessing_service_pb2.DESCRIPTOR.services_by_name['Preprocessing'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)
    server.add_insecure_port('[::]:8080')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()