# Zeus

FROM gdartifactory1.jfrog.io/docker-dcu-local/dcu-python3.11:1.1
LABEL MAINTAINER=dcueng@godaddy.com

USER root
WORKDIR /tmp

RUN mkdir -p /tmp/build
RUN apt-get update && apt-get install gcc libffi-dev -y
COPY requirements.txt /tmp/build/
COPY pip_config /tmp/build/pip_config
RUN PIP_CONFIG_FILE=/tmp/build/pip_config/pip.conf pip install -r /tmp/build/requirements.txt
RUN apt-get remove gcc libffi-dev -y

# Move files to new dir
COPY *.py /tmp/build/
COPY test_requirements.txt /tmp/build/
COPY README.md /tmp/build/
COPY certs /tmp/build/certs
COPY zeus /tmp/build/zeus
RUN PIP_CONFIG_FILE=/tmp/build/pip_config/pip.conf pip install --compile /tmp/build

RUN mkdir -p /app
COPY *.py logging.yaml *.sh /app/

RUN sed -i 's#MinProtocol = TLSv1.2#MinProtocol = TLSv1.0#g' /etc/ssl/openssl.cnf

# cleanup
RUN rm -rf /tmp/build
RUN chown dcu:dcu -R /app
WORKDIR /app
USER dcu
ENTRYPOINT [ "/usr/local/bin/celery", "-A", "run", "worker", "-l", "INFO", "--without-gossip", "--without-heartbeat", "--without-mingle" ]