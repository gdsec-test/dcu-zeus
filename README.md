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
git clone git@github.secureserver.net:ITSecurity/zeus.git
```

It is recommended that you clone this project into a pyvirtualenv or equivalent virtual environment.

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
All deploys must pass Flake8 linting and all unit tests which are baked into the [Makefile](Makfile).

There are a few commands that might be useful to ensure consistent Python style:

```
make flake8  # Runs the Flake8 linter
make isort   # Sorts all imports
make tools   # Runs both Flake8 and isort
```

## Running Locally
If you would like to run Zeus locally you will need to specify the following environment variables
 1. `sysenv` (dev, ote, prod)
 2. `DB_PASS` (MongoDB password for Phishstory database)
 3. `BROKER_PASS` (The Broker Pass for the RabbitMQ server to connect to)
 4. `MWPONEUSER` & `MWPONEPASS` (Account credentials to access the managed wordpress API)
 5. `DIABLOUSER` & `DIABLOPASS` (Account credentials to access the diablo API)
 6. `NETVIO_SSL_CERT` (The path to the SSL Cert white-listed for Netvio Soap API)
 7. `NETVIO_SSL_KEY` (The path to the SSL Key white-listed for Netvio Soap API)
 8. `OCM_SSL_CERT` (The path to the SSL Cert white-listed for OCM API)
 9. `OCM_SSL_KEY` (The path to the SSL Key white-listed for OCM API)
 10. `ZEUS_SSL_CERT` (The path to the SSL Cert for communicating with DCU Journal)
 11. `ZEUS_SSL_KEY` (The path to the SSL Key for communicating with DCU Journal)
 12. `EMAIL_RECIPIENT` (The email address you want `non-shopper` emails sent to while testing, instead of emailing fraud. e.g. user@example.com)
