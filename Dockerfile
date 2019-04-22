FROM alpine:3.9
MAINTAINER DCU ENG <DCUEng@godaddy.com>

RUN addgroup -S dcu && adduser -H -S -G dcu dcu
# apt-get installs
RUN apk update && \
    apk add --no-cache build-base \
    ca-certificates \
    python-dev \
    openssl-dev \
    libffi-dev \
    py-pip

WORKDIR /tmp

# Move files to new dir
ADD . /tmp

# pip install private pips staged by Makefile
RUN for entry in dcdatabase crm_notate hermes PyAuth; \
    do \
    pip install --compile "/tmp/private_pips/$entry"; \
    done

COPY certs/* /usr/local/share/ca-certificates/
RUN pip install --compile certifi
RUN pip install --compile -r requirements.txt
RUN pip install --compile .

RUN mkdir -p /app
COPY *.py logging.yml *.sh /app/
RUN /bin/sh -c "cat certs/* >> `python -c 'import certifi; print(certifi.where())'`"
RUN chown -R dcu:dcu /app && update-ca-certificates

# cleanup
RUN rm -rf /tmp

WORKDIR /app

ENTRYPOINT ["/app/runserver.sh"]