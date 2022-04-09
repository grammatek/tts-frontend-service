import sys
from os.path import dirname

sys.path.append(dirname(__file__)+'/generated/')

import logging
import grpc
from google.protobuf import empty_pb2
from generated.services import preprocessing_service_pb2_grpc
from generated.messages import preprocessing_message_pb2 as msg_pb2


def get_version(stub):
    response = stub.GetVersion(empty_pb2.Empty())
    print(response)


def get_clean_text(stub, text, html=False):
    message = msg_pb2.TextCleanRequest(content=text, parse_html=html)
    response = stub.Clean(message)
    print(response)
    print(response.processed_content)


def get_normalized_text(stub, text):
    norm_domain = msg_pb2.NormalizationDomain(norm_domain=msg_pb2.NORM_DOMAIN_SPORT)
    message = msg_pb2.NormalizeRequest(content=text, domain=norm_domain)
    response = stub.Normalize(message)
    print(response)
    print(response.processed_content)


def get_transcribed_text(stub, text, custom_dict={}, word_sep='', syllabified='', stress_labels=False):
    norm_domain = msg_pb2.NormalizationDomain(norm_domain=msg_pb2.NORM_DOMAIN_SPORT)
    phoneme_descr = msg_pb2.PhonemeDescription(word_separator=word_sep, syllabified=syllabified, stress_labels=stress_labels)
    message = msg_pb2.PreprocessRequest(content=text, domain=norm_domain, pronunciation_dict=custom_dict,
                                        description=phoneme_descr)
    response = stub.Preprocess(message)
    print(response)
    print(response.processed_content)


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


def get_custom_dict() -> dict:
    return {'eftir': 'E p t I r', 'sögðu': 's 9 k D Y'}

def run():
    with grpc.insecure_channel('localhost:8080') as channel:
        stub = preprocessing_service_pb2_grpc.PreprocessingStub(channel)
        print("-------------- GetVersion --------------")
        get_version(stub)
        #print("-------------- Clean --------------")
        #get_clean_text(stub, "en π námundast í 3.14")
        #print("-------------- Clean HTML --------------")
        #get_clean_text(stub, get_html_string(), html=True)
        #print("-------------- Normalize --------------")
        #get_normalized_text(stub, "það voru 55 km eftir")
        print("-------------- Transcribe --------------")
        get_transcribed_text(stub, "það voru 55 km eftir, sögðu allir nema 1", custom_dict=get_custom_dict())


if __name__=='__main__':
    logging.basicConfig()
    run()