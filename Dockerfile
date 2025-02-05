FROM python:3.12-alpine

WORKDIR /app

RUN apk update && \
    apk add git

ENV IN_DOCKER=true
ENV SCHEDULED=true

COPY . .

# install requirements
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "letterboxd_trakt.main"]
