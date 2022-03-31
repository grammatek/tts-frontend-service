# TTS Frontend Service

This is a gRPC service for a [TTS text preprocessing pipeline for Icelandic](https://github.com/grammatek/tts-frontend).

The service can be used for the whole pipeline: text extraction from html, text cleaning, text normalization for TTS,
spell correction, insertion of pause labels through phrasing, and finally grapheme-to-phoneme conversion (g2p).
The pipeline is developed to be a frontend module for a speech synthesis system (TTS) where raw text is processed 
and converted to the appropriate format used by the system at hand. However, it can also be used for text cleaning or
normalization only.

When using the whole pipeline, the html-parsing, spell correction and phrasing are optional, text cleaning,
normalization and g2p are mandatory.

## Setup

Clone the repository and update submodule:

```
$ git clone https://github.com/grammatek/tts-frontend-service.git
$ git submodule update --init
```

Create and start a virtual environment and install requirements:

```
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
```

Try the service from the command line

```
# start the service (to stop: ctrl-C)
(venv)$ python3 src/tts_frontend_server.py

# in another terminal, run the example client:
(venv)$ python3 src/tts_frontend_client_example.py

```

Build the Docker image

```
$ docker build -t tts-frontend-service:latest .
```

