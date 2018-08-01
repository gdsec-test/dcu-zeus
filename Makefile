REPONAME=infosec-dcu/zeus
BUILDROOT=$(HOME)/dockerbuild/$(REPONAME)
DOCKERREPO=docker-dcu-local.artifactory.secureserver.net/zeus
DATE=$(shell date)

# libraries we need to stage for pip to install inside Docker build
PRIVATE_PIPS=git@github.secureserver.net:ITSecurity/dcdatabase.git \
git@github.secureserver.net:ITSecurity/crm_notate.git \
git@github.secureserver.net:ITSecurity/hermes.git

.PHONY: prep dev stage prod ote clean prod-deploy ote-deploy dev-deploy

all: prep dev

prep:
	@echo "----- preparing $(REPONAME) build -----"
	# stage pips we will need to install in Docker build
	mkdir -p $(BUILDROOT)/private_pips && rm -rf $(BUILDROOT)/private_pips/*
	for entry in $(PRIVATE_PIPS) ; do \
		cd $(BUILDROOT)/private_pips && git clone $$entry ; \
	done

	# copy the app code to the build root
	cp -rp ./* $(BUILDROOT)

stage: prep
	@echo "----- building $(REPONAME) stage -----"
	DOCKERTAG=stage
	docker build -t $(DOCKERREPO):stage $(BUILDROOT)

prod: prep
	@echo "----- building $(REPONAME) prod -----"
	  read -p "About to build production image from $(BUILD_BRANCH) branch. Are you sure? (Y/N): " response ; \
	  if [[ $$response == 'N' || $$response == 'n' ]] ; then exit 1 ; fi
	  if [[ `git status --porcelain | wc -l` -gt 0 ]] ; then echo "You must stash your changes before proceeding" ; exit 1 ; fi
	  git fetch && git checkout $(BUILD_BRANCH)
	  $(eval COMMIT:=$(shell git rev-parse --short HEAD))
	  sed -ie 's/THIS_STRING_IS_REPLACED_DURING_BUILD/$(DATE)/' $(BUILDROOT)/k8s/prod/zeus.deployment.yml
	  sed -ie 's/REPLACE_WITH_GIT_COMMIT/$(COMMIT)/' $(BUILDROOT)/k8s/prod/zeus.deployment.yml
	  docker build -t $(DOCKERREPO):$(COMMIT) $(BUILDROOT)
	  git checkout -

ote: prep
	@echo "----- building $(REPONAME) ote -----"
	sed -ie 's/THIS_STRING_IS_REPLACED_DURING_BUILD/$(DATE)/g' $(BUILDROOT)/k8s/ote/zeus.deployment.yml
	docker build -t $(DOCKERREPO):ote $(BUILDROOT)

dev: prep
	@echo "----- building $(REPONAME) dev -----"
	sed -ie 's/THIS_STRING_IS_REPLACED_DURING_BUILD/$(DATE)/g' $(BUILDROOT)/k8s/dev/zeus.deployment.yml
	docker build -t $(DOCKERREPO):dev $(BUILDROOT)

prod-deploy: prod
	@echo "----- deploying $(REPONAME) prod -----"
	docker push $(DOCKERREPO):$(COMMIT)
	kubectl --context prod apply -f $(BUILDROOT)/k8s/prod/zeus.deployment.yml --record

ote-deploy: ote
	@echo "----- deploying $(REPONAME) ote -----"
	docker push $(DOCKERREPO):ote
	kubectl --context ote apply -f $(BUILDROOT)/k8s/ote/zeus.deployment.yml --record

dev-deploy: dev
	@echo "----- deploying $(REPONAME) dev -----"
	docker push $(DOCKERREPO):dev
	kubectl --context dev apply -f $(BUILDROOT)/k8s/dev/zeus.deployment.yml --record

clean:
	@echo "----- cleaning $(REPONAME) app -----"
	rm -rf $(BUILDROOT)