# pigss-launcher

# Let's be strict about the shell we're using
# If we ever get fancy and don't use a Debian-based amd64 system
# with /bin/sh installed we'll have to re-factor a bit.
SHELL:=/bin/sh
LOGO_DIR=/usr/local/share/picarro/icons
INSTALL_DIR=/tmp/pigss-launcher
BUILD_DIR=dist
DEB_BUILD_DIR=${BUILD_DIR}/.debian
# BUILD_NUMBER can be overridden by passing in a build number
# 		$ make deb BUILD_NUMBER=1.2.3
BUILD_NUMBER=0.0.1
GIT_HASH=$(shell git rev-parse --short HEAD)
# Assets to include in the Debian file
ASSETS=assets/pigss-launcher.desktop assets/pigss-auto-launcher.desktop
LOGO=assets/picarro_logo.svg

# Meta data for DEBIAN/control
# PACKAGE_NAME can be overriden by passing in a name
#		$ make deb BUILD_NUMBER=1.2.3 PACKAGE_NAME=pigss-launcher-dev
PACKAGE_NAME=pigss-launcher
VERSION=${BUILD_NUMBER}
ARCHITECTURE=amd64
MAINTAINER=gsornsen@picarro.com
PRIORITY=optional
DESCRIPTION=Launches browser to PiGSS Software

# Make the debian package
.PHONY: deb
deb: clean deb-dirs prerm postinst control
	dpkg-deb --build ${DEB_BUILD_DIR} ${BUILD_DIR}/${PACKAGE_NAME}-${VERSION}.deb

.PHONY: deb-dirs
deb-dirs:
	@ mkdir -p ${DEB_BUILD_DIR}
	@ mkdir -p ${DEB_BUILD_DIR}${INSTALL_DIR}
	@ mkdir -p ${DEB_BUILD_DIR}${LOGO_DIR}
	@ cp -r ${ASSETS} ${DEB_BUILD_DIR}${INSTALL_DIR}
	@ cp -rv ${LOGO} ${DEB_BUILD_DIR}${LOGO_DIR}

# Write the control file
.PHONY: control
control:
	@ mkdir -p ${DEB_BUILD_DIR}/DEBIAN
	@ echo "Package: ${PACKAGE_NAME}\n\
	Architecture: ${ARCHITECTURE}\n\
	Maintainer: ${MAINTAINER}\n\
	Priority: ${PRIORITY}\n\
	Version: ${VERSION}\n\
	Installed-size: `du -s ${DEB_BUILD_DIR} | cut -f1`\n\
	Description: ${DESCRIPTION}\n" > ${DEB_BUILD_DIR}/DEBIAN/control

# Copy prerm script
.PHONY: prerm
prerm:
	@ mkdir -p ${DEB_BUILD_DIR}/DEBIAN
	@ cp -r DEBIAN/prerm ${DEB_BUILD_DIR}/DEBIAN/prerm

# Copy postinst script
.PHONY: postinst
postinst:
	@ mkdir -p ${DEB_BUILD_DIR}/DEBIAN
	@ cp -r DEBIAN/postinst ${DEB_BUILD_DIR}/DEBIAN/postinst

.PHONY: clean
clean:
	rm -rfv dist
