# Zeus

FROM docker-dcu-local.artifactory.secureserver.net/dcu-python3.7:3.3
LABEL MAINTAINER=dcueng@godaddy.com

USER root
WORKDIR /tmp

# Move files to new dir
ADD . /tmp

RUN PIP_CONFIG_FILE=/tmp/pip_config/pip.conf pip install --compile /tmp

RUN mkdir -p /app
COPY *.py logging.yaml *.sh /app/

RUN chown dcu:dcu -R /app

RUN sed -i 's#MinProtocol = TLSv1.2#MinProtocol = TLSv1.0#g' /etc/ssl/openssl.cnf

# cleanup
RUN rm -rf /tmp


WORKDIR /app
USER dcu
ENTRYPOINT [ "/usr/local/bin/celery", "-A", "run", "worker", "-l", "INFO", "--without-gossip", "--without-heartbeat", "--without-mingle" ]