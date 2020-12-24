# building rumor
FROM golang:alpine as build

RUN apk add --no-cache ca-certificates build-base

WORKDIR /build

ADD rumor .

RUN CGO_ENABLED=1 GOOS=linux \
    go build -ldflags '-extldflags "-w -s -static"' -o app

# main container
FROM python:3.8-slim-buster

COPY --from=build /build/app /rumor

WORKDIR /app

COPY requirements.txt .
RUN apt-get update \
 && apt-get install -qq -y \
    gcc \
 && pip3 install --no-cache-dir --upgrade pip wheel setuptools \
 && pip3 install --no-cache-dir -r requirements.txt

# Launch
COPY connect.py .
ENTRYPOINT ["python3"]
# CMD ["connect.py"]
