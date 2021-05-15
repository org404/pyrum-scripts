FROM ubuntu:18.04 as radamsa-builder
RUN apt-get update -qq \
 && apt-get install -qq -y gcc git make wget

RUN git clone https://gitlab.com/akihe/radamsa.git \
 && cd radamsa \
 && make \
 && make install


FROM python:3.9-slim-buster as fuzzer
WORKDIR /app
COPY --from=radamsa-builder /usr/bin/radamsa /usr/bin/radamsa

COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip wheel setuptools \
 && pip3 install --no-cache-dir -r requirements.txt

COPY radamsa.py .
ENTRYPOINT ["python3", "radamsa.py"]
