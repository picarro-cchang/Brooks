# pigss-core

# Let's be strict about the shell we're using
# If we ever get fancy and don't use a Debian-based amd64 system
# with /bin/sh installed we'll have to re-factor a bit.
SHELL:=/bin/sh

SOURCE_DIR=../../
SOURCE_CONFIGS=${SOURCE_DIR}back_end
SIMULATION_CONFIGS=${SOURCE_DIR}simulation
INSTALL_DIR=/usr/bin
CONFIG_INSTALL_DIR=/tmp/config/pigss-core
SERVICE_INSTALL_DIR=/etc/systemd/system
TIME_INSTALL_DIR=/usr/local/share/picarro
BUILD_DIR=dist
DEB_BUILD_DIR=${BUILD_DIR}/.debian
# BUILD_NUMBER can be overridden by passing in a build number
# 		$ make deb BUILD_NUMBER=1.2.3
BUILD_NUMBER=0.0.1
GIT_HASH=$(shell git rev-parse --short HEAD)
# Assets to include in the Debian file
ASSETS=${BUILD_DIR}/pigss-core
CONFIG_ASSETS=${SOURCE_CONFIGS}/*.yaml ${SOURCE_CONFIGS}/*.json ${SIMULATION_CONFIGS}/*.json
SERVICE_ASSETS=systemd/pigss-core.service
TIME_ASSETS=${SOURCE_DIR}back_end/time_synchronization/setup_client.py

# Meta data for DEBIAN/control
# PACKAGE_NAME can be overriden by passing in a name
#		$ make deb BUILD_NUMBER=1.2.3 PACKAGE_NAME=pigss-core-dev
PACKAGE_NAME=pigss-core
VERSION=${BUILD_NUMBER}
ARCHITECTURE=amd64
MAINTAINER=gsornsen@picarro.com
PRIORITY=optional
DESCRIPTION=Core Code for PiGSS
DEPENDS=avrdude

# Make the debian package
.PHONY: deb
deb: clean binary deb-dirs prerm postinst control
	dpkg-deb --build ${DEB_BUILD_DIR} ${BUILD_DIR}/${PACKAGE_NAME}-${VERSION}.deb

# Make the directories necessary for the debian package
.PHONY: deb-dirs
deb-dirs:
	@ mkdir -p ${DEB_BUILD_DIR}${INSTALL_DIR}
	@ mkdir -p ${DEB_BUILD_DIR}${CONFIG_INSTALL_DIR}
	@ mkdir -p ${DEB_BUILD_DIR}${SERVICE_INSTALL_DIR}
	@ mkdir -p ${DEB_BUILD_DIR}${TIME_INSTALL_DIR}
	@ cp -r ${ASSETS} ${DEB_BUILD_DIR}${INSTALL_DIR}
	@ cp -rv ${CONFIG_ASSETS} ${DEB_BUILD_DIR}${CONFIG_INSTALL_DIR}
	@ cp -rv ${SERVICE_ASSETS} ${DEB_BUILD_DIR}${SERVICE_INSTALL_DIR}
	@ cp -rv ${TIME_ASSETS} ${DEB_BUILD_DIR}${TIME_INSTALL_DIR}

# Make the pigss-core binary file
.PHONY: binary
binary:
	pyinstaller pigss-core.spec --workpath /tmp

# Write the control file
.PHONY: control
control:
	@ mkdir -p ${DEB_BUILD_DIR}/DEBIAN
	@ echo "Package: ${PACKAGE_NAME}\n\
	Architecture: ${ARCHITECTURE}\n\
	Maintainer: ${MAINTAINER}\n\
	Priority: ${PRIORITY}\n\
	Version: ${VERSION}\n\
	Depends: ${DEPENDS}\n\
	Installed-size: `du -s ${DEB_BUILD_DIR} | cut -f1`\n\
	Description: ${DESCRIPTION}\n" > ${DEB_BUILD_DIR}/DEBIAN/control

# Write prerm script
.PHONY: prerm
prerm:
	@ mkdir -p ${DEB_BUILD_DIR}/DEBIAN
	@ cp -r DEBIAN/prerm ${DEB_BUILD_DIR}/DEBIAN/prerm

# Write postinst script
.PHONY: postinst
postinst:
	@ mkdir -p ${DEB_BUILD_DIR}/DEBIAN
	@ cp -r DEBIAN/postinst ${DEB_BUILD_DIR}/DEBIAN/postinst

.PHONY: clean
clean:
	rm -rfv dist
	rm -rfv /tmp/pigss-core*
