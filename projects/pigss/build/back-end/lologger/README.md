# Build lologger

## Local Build

```bash
make deb
```

`lologger-0.0.1.deb` will be placed in the dist folder
***

## CI/CD Integration

### Available Parameters

* BUILD_NUMBER
* PACKAGE_NAME

#### Examples

```bash
make deb BUILD_NUMBER=1.0.0
```

`lologger-1.0.0.deb` will be placed in the dist folder

***

```bash
make deb BUILD_NUMBER=1.0.0 PACKAGE_NAME=lologger-dev
```

`lologger-dev-1.0.0.deb` will be placed in the dist folder

#### Control Files

Passing in the BUILD_NUMBER of PACKAGE_NAME modifies the control file allowing you to _technically_ have both lologger and lologger-dev installed on the machine. Really the purpose it to allow the CI/CD server to build dev packages that we pass around internally for development/testing and is built from develop/topic branches. The lologger packages will be reserved for building tagged releases from the master branch.

#### Control File Examples

```bash
Package: lologger
Architecture: amd64
Maintainer: gsornsen@picarro.com
Priority: optional
Version: 0.0.1
Installed-size: 9256
Description: RPC based logger for PiGSS
```

```bash
Package: lologger
Architecture: amd64
Maintainer: gsornsen@picarro.com
Priority: optional
Version: 1.0.0
Installed-size: 9256
Description: RPC based logger for PiGSS
```

```bash
Package: lologger-dev
Architecture: amd64
Maintainer: gsornsen@picarro.com
Priority: optional
Version: 1.0.0
Installed-size: 9256
Description: RPC based logger for PiGSS
```
