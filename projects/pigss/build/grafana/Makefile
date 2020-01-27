# grafana

SHELL:=/bin/sh
# Let's be strict about the shell we're using

# With some light re-factoring we can leverage fpm to do cross-compilation
# to support Mac/Windows and create RPM packages. We're settling with Debian only
# for PiGSS. Should we decide to port "Picarro" Grafana for more projects, we should
# recycle this work and make this slightly more complex.
PATH:=/usr/local/go/bin:${PATH}
export GOPATH=${HOME}/go
REPO_ROOT_DIR=${HOME}/git/host
GRAFANA_ROOT_DIR=${REPO_ROOT_DIR}/projects/pigss/front_end/grafana/src/grafana
CWD=${PWD}

.PHONY: deb
deb: submodule setup
	@ cd ${GRAFANA_ROOT_DIR} && go run build.go build pkg-deb
	@ cp -r ${GRAFANA_ROOT_DIR}/dist ${CWD}/dist

.PHONY: submodule
submodule:
	@ cd ${REPO_ROOT_DIR}
	@ git submodule init

.PHONY: go
go:
	@ if [ ! -d /usr/local/go ]; then wget https://dl.google.com/go/go1.12.1.linux-amd64.tar.gz -P /tmp && sudo tar -C /usr/local -xzf /tmp/go*.tar.gz; fi

.PHONY: setup
setup: go
	@ cd ${GRAFANA_ROOT_DIR} && go run build.go setup
	@ cd ${GRAFANA_ROOT_DIR} && yarn install --pure-lockfile

.PHONY: test
test: setup
	@ # TODO: Fix Grafana's failing tests
	@ echo "\n#####################\nTesting Front-End\n#####################\n"
	@ cd ${GRAFANA_ROOT_DIR} && npm run test
	@ echo "n#####################\nTesting Back-Endn#####################\n"
	@ cd ${GRAFANA_ROOT_DIR} && go run build.go test

.PHONY: clean
clean:
	@ cd ${GRAFANA_ROOT_DIR} && go run build.go clean
	@ rm -rfv ${CWD}/dist
