FROM python:3.13-alpine

WORKDIR /app

RUN apk update && \
    apk add git

ENV IN_DOCKER=true
ENV SCHEDULED=true

COPY . .

# install requirements
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-u", "-m", "letterboxd_trakt.main"]
