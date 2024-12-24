FROM python:3.12-alpine

WORKDIR /app

RUN apk update && \
    apk add git

ENV IN_DOCKER=true

# install requirements
COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./letterboxd_trakt ./letterboxd_trakt
COPY ./docker ./docker

CMD ./docker/entrypoint.sh
