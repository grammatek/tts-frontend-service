import sys
from os.path import dirname
from typing import List, Tuple

sys.path.append(dirname(__file__)+'/generated/')

import logging
import grpc
from google.protobuf import empty_pb2
from generated.services import preprocessing_service_pb2_grpc
from generated.messages import preprocessing_message_pb2 as msg_pb2


def get_version(stub):
    response = stub.GetVersion(empty_pb2.Empty())
    return response


def get_default_params(stub):
    response = stub.GetDefaultParameters(empty_pb2.Empty())
    return response


def get_clean_text(stub, text, html=False):
    message = msg_pb2.TextCleanRequest(content=text, parse_html=html)
    response = stub.Clean(message)
    return response


def get_normalized_text(stub, text, parse_html=False):
    norm_domain = msg_pb2.NormalizationDomain(norm_domain=msg_pb2.NORM_DOMAIN_SPORT)
    message = msg_pb2.NormalizeRequest(content=text, domain=norm_domain)
    response = stub.Normalize(message)

    sentences_with_pairs: List[List[Tuple[str, str]]] = []
    curr_sent = []
    for norm_token in response.tokens:
        if norm_token.HasField("normalized"):
            print("normalized: " + norm_token.normalized.name)
        if norm_token.HasField("tag"):
            print("tag: " + norm_token.tag.name)

        if norm_token.HasField("tag"):
            if norm_token.tag.name == '<sentence>':
                sentences_with_pairs.append(curr_sent)
                curr_sent = []
            else:
                # this is a tag-token representing a pause, don't deal with that right now
                continue
        elif norm_token.HasField("normalized"):
            original = norm_token.normalized.clean_token.original_token.name
            normalized = norm_token.normalized.name
            curr_sent.append((original, normalized))

    if curr_sent:
        sentences_with_pairs.append(curr_sent)
    return sentences_with_pairs


def get_transcribed_text(stub, text, parse_html=False, custom_dict={}, dialect=msg_pb2.DIALECT_STANDARD, word_sep='',
                         syllabified='', stress_labels=False, no_tag_tokens_in_content=False):
    """
    Compose a PreprocessRequest from the parameters and send to the Preprocess service.
    TODO: Dialect param is not acutally available yet, only the DIALECT_STANDARD. Add DIALECT_NORTH to implementation
    """
    norm_domain = msg_pb2.NormalizationDomain(norm_domain=msg_pb2.NORM_DOMAIN_SPORT)
    norm_message = msg_pb2.NormalizeRequest(content=text, domain=norm_domain)
    phoneme_descr = msg_pb2.PhonemeDescription(dialect=dialect, word_separator=word_sep, syllabified=syllabified,
                                               stress_labels=stress_labels)
    message = msg_pb2.PreprocessRequest(content=text, norm_request=norm_message, pronunciation_dict=custom_dict,
                                        description=phoneme_descr, no_tag_tokens_in_content=no_tag_tokens_in_content, parse_html=parse_html)
    response = stub.Preprocess(message)
    return response


def get_html_string():
    return '<p id="hix00274"><span id="qitl_0591" class="sentence">Í kjölfarið sýndi hann fram á að það stuðli að ' \
               'heilbrigði ef einstaklingar geti fundið samhengi í tengslum við lífsatburði eða öðlast skilning á aðstæðum sínum. ' \
               '</span><span id="qitl_0592" class="sentence">Hann taldi uppsprettu heilbrigðis ' \
               '(e. </span><em><span id="qitl_0593" class="sentence">salutogenesis)</span></em><span id="qitl_0594" class="sentence"> ' \
               'vera að finna í mismunandi hæfni einstaklinga til að stjórna viðbrögðum sínum við álagi. </span>' \
               '<span id="qitl_0595" class="sentence">Antonovsky sýndi fram á að ef einstaklingar sem upplifðu álag sæju ' \
               'tilgang með reynslu sinni, þá þróaðist með þeim tilfinning fyrir samhengi í lífinu ' \
               '(e. </span><em><span id="qitl_0596" class="sentence">sense of coherence).</span></em>' \
               '<span id="qitl_0597" class="sentence"> Sigrún Gunnarsdóttir hefur íslenskað skilgreiningu hugtaksins ' \
               'um tilfinningu fyrir samhengi í lífinu á eftirfarandi hátt: </span></p>'


def get_html_string_with_non_valid_chars():
    return '<p>o Hugleiða að ráða tímabundið starfsmann í þessa vinnu</p> ' \
           '<p>· Við þurfum að hafa texta og hljóð af sömu bókum sem hægt er að nota til að búa til aðgengilegar bækur</p>' \
           '<p>o Hversu margar bækur þarf?</p>' \
           '<p>§ Því fleiri, því betri</p>'

def get_custom_dict() -> dict:
    return {'eftir': 'E p t I r', 'sögðu': 's 9 k D Y'}

def run():
    with grpc.insecure_channel('localhost:8080') as channel:
        stub = preprocessing_service_pb2_grpc.PreprocessingStub(channel)
        print("-------------- GetVersion --------------")
        response = get_version(stub)
        print(response)
        print("-------------- GetDefaultParams --------")
        response = get_default_params(stub)
        print("norm params: \n" + str(response.normalization_params))
        print("g2p params: \n" + str(response.phoneme_description))
        print("-------------- Clean --------------")
        get_clean_text(stub, "en π námundast í 3.14")
        print("-------------- Clean HTML --------------")
        html_parsed_response = get_clean_text(stub, get_html_string(), html=True)
        print(html_parsed_response.processed_content)
        print("-------------- Normalize --------------")
        normalized_response = get_normalized_text(stub, "Það voru 55 km eftir. Sagði þjálfari ÍA.")
        print(normalized_response)
        print("-------------- Transcribe --------------")

        transcribed_response = get_transcribed_text(stub, get_html_string(), parse_html=True, custom_dict=get_custom_dict(),
                             syllabified='', word_sep='', stress_labels=False, no_tag_tokens_in_content=False)

        print(transcribed_response.processed_content)
        print("-------------- Transcribe 2--------------")

        transcribed_response = get_transcribed_text(stub, get_html_string_with_non_valid_chars(), parse_html=True,
                                                    custom_dict=get_custom_dict(),
                                                    syllabified='', word_sep='', stress_labels=False,
                                                    no_tag_tokens_in_content=False)

        print(transcribed_response.processed_content)


if __name__=='__main__':
    logging.basicConfig()
    run()