# Zeus

Zeus is responsible for facilitating automated actions on GoDaddy Products. 
These are mainly broken up into 1) Registered 2) Hosted) and 3) Fraud actions. Its major functionality currently include
 1. Product Suspensions (Domains, cPanel, MWP 1.0, etc.)
 2. Customer Warnings (Domains, Vertigo)
 
In the future, Zeus will be extended to interact with DCU Journal to help publish events for Hosting Product Team and other entities
to consume. This will aid in the decentralization of abuse management at GoDaddy.

## Cloning
To clone the repository via SSH perform the following
```
git clone git@github.secureserver.net:digital-crimes/zeus.git
```

It is recommended that you clone this project into a pyvirtualenv or equivalent virtual environment. For this project,
be sure to create a virtual environment with Python 3.
This is achievable via `mkproject --python=$(asdf where python)/bin/python zeus`

## Installing Dependencies
To install all dependencies for development and testing simply run `make`.

## Building
Building a local Docker image for the respective development environments can be achieved by
```
make [dev, ote, prod]
```

## Deploying
Deploying the Docker image to Kubernetes can be achieved via
```
make [dev, ote, prod]-deploy
```
You must also ensure you have the proper push permissions to Artifactory or you may experience a `Forbidden` message.

## Testing
```
make test     # runs all unit tests
make testcov  # runs tests with coverage
```

## Style and Standards
All deploys must pass Flake8 linting and all unit tests which are baked into the [Makefile](Makefile).

There are a few commands that might be useful to ensure consistent Python style:

```
make flake8  # Runs the Flake8 linter
make isort   # Sorts all imports
make tools   # Runs both Flake8 and isort
```

## Certs Required
The following certs are required to run this project, must include proper ENV domain:
 1. `OCM API`: phishstory.int.
 2. `ZEUS DCU Journal`: dcu.zeus.int.
 3. `Ecomm/Orion Web Service`: dcu.ecomm.
 
## Running Locally
### Docker-compose, local docker images zeus redis, and rabbitmq, with dev mongo

Environment variables for docker-compose.yml file:
1. `DB_PASS` (Password for dev MongoDB)
2. `BROKER_PASS` (Broker Password)
3. `DIABLOUSER` & `DIABLOPASS` (Account credentials to access the diablo API)
4. `MWPONEUSER` & `MWPONEPASS` (Account credentials to access the managed wordpress API)
5. `PLESKUSER` & `PLESKPASS` (Account credentials to access the plesk API)
6. `VPS4USER` & `VPS4PASS` (Account credentials to access the vps4 API)
7. `CMAP_PROXY_PASS` & `CMAP_PROXY_PASS` (Account credentials to access theCMAP Proxy)
8. `EMAIL_RECIPIENT` (The email address you want `non-shopper` emails sent to while testing, instead of emailing fraud. e.g. user@example.com)  *** *ONLY WORKS WITH TEMPLATES THAT SEND TO NON-SHOPPERS* ***

Changes to docker-compose.yml file:
* Run `docker-compose up -d` to run zeus, rabbitmq and redis locally in a docker container.
* Run `docker logs -f <Zeus docker name>` to view the run logs for auto_abuse_id
* Run `docker logs -f <Redis docker name>` to view the run logs for dcu-classifier
* Run `docker logs -f <RabbitMq docker name>` to view the run logs for rabbitmq
* Run `redis-cli` to interact with your local REDIS instance
* Browse to `127.0.0.1:15672` with creds `guest:guest` to view the management console for your local RabbitMQ
* Run `tests/integration_script.py` to publish different tasks to the local RabbitMQ devzeus queue

If you would like to run Zeus locally you will need to specify the following environment variables in an IDE like Pycharm
* `sysenv` (dev, ote, prod)
* `DISABLESSL` (True)
* `DB_PASS` (MongoDB password for Phishstory database)
* `BROKER_PASS` (The Broker Pass for the RabbitMQ server to connect to)
* `BROKER_URL` (amqp://guest@localhost:5672//)
* `MWPONEUSER` & `MWPONEPASS` (Account credentials to access the managed wordpress API)
* `DIABLOUSER` & `DIABLOPASS` (Account credentials to access the diablo API)
* `PLESKUSER` & `PLESKPASS` (Account credentials to access the plesk API)
* `VPS4USER` & `VPS4PASS` (Account credentials to access the vps4 API)
* `GOCENTRAL_URL` SOAP URL for adding Orion event for suspending GoCentral guid
* `GOCENTRAL_SSL_CERT` (The path to the SSL Cert white-listed for Orion Web Service `dcu.ecomm.dev.authclient.int.godaddy.com` dev/test use dev, prod uses prod)
* `GOCENTRAL_SSL_KEY` (The path to the SSL Key white-listed for Orion Web Service `dcu.ecomm.dev.authclient.int.godaddy.com` dev/test use dev, prod uses prod)
* `CMAP_PROXY_CERT` Path to certificate file (for connecting to CMAP Proxy `proxyuser.cmap.int.godaddy.com` prod only)
* `CMAP_PROXY_KEY` Path to key file(for connecting to CMAP Proxy `proxyuser.cmap.int.godaddy.com`  prod only)
* `CMAP_PROXY_USER` (User for CMAP Proxy)
* `CMAP_PROXY_PASS` (Password for CMAP Proxy)
* `OCM_SSL_CERT` (The path to the SSL Cert white-listed for OCM API `phishstory.int.`)
* `OCM_SSL_KEY` (The path to the SSL Key white-listed for OCM API `phishstory.int.`)
* `ORION_SSL_CERT` (The path to the SSL Cert white-listed for Orion Web Service `dcu.ecomm.dev.authclient.int.godaddy.com` prod only)
* `ORION_SSL_KEY` (The path to the SSL Key white-listed for Orion Web Service `dcu.ecomm.dev.authclient.int.godaddy.com` prod only)
* `ZEUS_SSL_CERT` (The path to the SSL Cert for communicating with CRM Alert, DCU Journal, Mimir and Shoplocked `dcu.zeus.int`)
* `ZEUS_SSL_KEY` (The path to the SSL Key for communicating with CRM Alert, DCU Journal, Mimir and Shoplocked `dcu.zeus.int`)
* `EMAIL_RECIPIENT` (The email address you want `non-shopper` emails sent to while testing, instead of emailing fraud. e.g. user@example.com)  *** *ONLY WORKS WITH TEMPLATES THAT SEND TO NON-SHOPPERS* ***
* Run `docker-compose up -d rabbitmq redis` to run rabbitmq and redis locally in a docker container.
* PyCharm script path will need to be set to: `/PATH_TO_ZEUS_ENVS/bin/celery`.
* PyCharm parameters will need to be set to: `-A run worker -l debug -P solo`
 
## Handling failures to create Mimir Infractions in Production.
1. Create dictionary of required infraction fields. Data will come from mongo record for the ticket. Majority of data in `data>domainQuery>host`
```
    {"shopperId" : "<shopper number>",
    "ticketId" : "<DCU ticket number>",
    "sourceDomainOrIp" : "<domain or ip>",
    "hostingGuid" : "<hosting guid>",
    "infractionType" : "<One of CONTENT_REMOVED, CUSTOMER_WARNING, EXTENSIVE_COMPROMISE, INTENTIONALLY_MALICIOUS, REPEAT_OFFENDER, SHOPPER_COMPROMISE or SUSPENDED">}
```

2. Obtain Prod JWT from Zeus Cert. Visit [this page](https://confluence.godaddy.com/pages/viewpage.action?pageId=127801950) for instructions
3. Send curl request to Mimir. Example below.
    ```
    curl -XPOST -H 'Content-Type: application/json' -H 'Authorization: sso-jwt <Zeus Cert2JWT>' https://mimir.int.godaddy.com/v1/infractions -d '{"shopperId" : "123456789", "ticketId" : "DCU123456789", "sourceDomainOrIp" : "example.com", "hostingGuid" : "abc-123-def-456-ghi789", "infractionType" : "CUSTOMER_WARNING"}'
    ```
4. Be sure you get an infraction ID back. You do not need to do anything with it, just confirming it was submitted.
