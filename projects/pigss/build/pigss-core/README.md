# Build pigss-core

## Local Build

```bash
make deb
```

`pigss-core-0.0.1.deb` will be placed in the dist folder
***

## CI/CD Integration

### Available Parameters

* BUILD_NUMBER
* PACKAGE_NAME

#### Examples

```bash
make deb BUILD_NUMBER=1.0.0
```

`pigss-core-1.0.0.deb` will be placed in the dist folder

***

```bash
make deb BUILD_NUMBER=1.0.0 PACKAGE_NAME=pigss-core-dev
```

`pigss-core-dev-1.0.0.deb` will be placed in the dist folder

#### Control Files

Passing in the BUILD_NUMBER of PACKAGE_NAME modifies the control file allowing you to _technically_ have both pigss-core and pigss-core-dev installed on the machine. Really the purpose it to allow the CI/CD server to build dev packages that we pass around internally for development/testing and is built from develop/topic branches. The pigss-core packages will be reserved for building tagged releases from the master branch.

#### Control File Examples

```bash
Package: pigss-core
Architecture: amd64
Maintainer: gsornsen@picarro.com
Priority: optional
Version: 0.0.1
Installed-Size: 415 MB
Depends: avrdude
Description: RPC based logger for PiGSS
```

```bash
Package: pigss-core
Architecture: amd64
Maintainer: gsornsen@picarro.com
Priority: optional
Version: 1.0.0
Installed-Size: 415 MB
Depends: avrdude
Description: RPC based logger for PiGSS
```

```bash
Package: pigss-core-dev
Architecture: amd64
Maintainer: gsornsen@picarro.com
Priority: optional
Version: 1.0.0
Installed-Size: 415 MB
Depends: avrdude
Description: RPC based logger for PiGSS
```
