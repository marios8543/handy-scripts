FROM python:alpine3.7

RUN apk add build-base
RUN apk add libffi-dev
RUN apk add openssl-dev
RUN apk add python3-dev

COPY . /app
WORKDIR /app
ENV interval 300

RUN pip install -r requirements.txt

CMD python3 animebyter.py