# syntax=docker/dockerfile:1
FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED=1
ENV TTS_FRONTEND=/tts_frontend_service

RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools
RUN apt-get update && apt-get install -y git

WORKDIR $TTS_FRONTEND

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . $TTS_FRONTEND

EXPOSE 8080

CMD ["python3", "src/tts_frontend_server.py"]