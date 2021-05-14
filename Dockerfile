# Zeus

FROM python:3.7.10-slim
LABEL MAINTAINER=dcueng@godaddy.com

RUN addgroup dcu && adduser --disabled-password --disabled-login --no-create-home --ingroup dcu --system dcu

WORKDIR /tmp

# Move files to new dir
ADD . /tmp

# pip install private pips staged by Makefile
RUN pip install --compile /tmp/private_pips/dcdatabase
RUN pip install --compile /tmp/private_pips/crm_notate
RUN pip install --compile /tmp/private_pips/hermes
RUN pip install --compile /tmp/private_pips/PyAuth
RUN pip install --compile /tmp/private_pips/dcu-structured-logging-celery
RUN pip install --compile /tmp

COPY certs/* /usr/local/share/ca-certificates/
RUN pip install --compile certifi
RUN pip install --compile -r requirements.txt
RUN pip install --compile .

RUN mkdir -p /app
COPY *.py logging.yaml *.sh /app/
RUN /bin/sh -c "cat certs/* >> `python -c 'import certifi; print(certifi.where())'`"
RUN chown -R dcu:dcu /app && update-ca-certificates
RUN sed -i 's#MinProtocol = TLSv1.2#MinProtocol = TLSv1.0#g' /etc/ssl/openssl.cnf

# cleanup
RUN rm -rf /tmp

WORKDIR /app

ENTRYPOINT ["/app/runserver.sh"]