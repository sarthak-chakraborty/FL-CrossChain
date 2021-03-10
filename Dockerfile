FROM python:3.6.10-slim

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  gcc
WORKDIR /app
RUN pip install --upgrade pip
RUN pip install confluent-kafka six requests pymongo tensorflow numpy pillow image-classifiers scipy
ADD . /app
