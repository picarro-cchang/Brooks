# Build pigss-mfg

## Local Build

```bash
make deb
```

`pigss-mfg-0.0.1.deb` will be placed in the dist folder
***

## CI/CD Integration

### Available Parameters

* BUILD_NUMBER
* PACKAGE_NAME

#### Examples

```bash
make deb BUILD_NUMBER=1.0.0
```

`pigss-mfg-1.0.0.deb` will be placed in the dist folder

***

```bash
make deb BUILD_NUMBER=1.0.0 PACKAGE_NAME=pigss-mfg-dev
```

`pigss-mfg-dev-1.0.0.deb` will be placed in the dist folder

#### Control Files

Passing in the BUILD_NUMBER of PACKAGE_NAME modifies the control file allowing you to _technically_ have both pigss-mfg and pigss-mfg-dev installed on the machine. Really the purpose it to allow the CI/CD server to build dev packages that we pass around internally for development/testing and is built from develop/topic branches. The pigss-mfg packages will be reserved for building tagged releases from the master branch.

#### Control File Examples

```bash
Package: pigss-mfg
Architecture: amd64
Maintainer: gsornsen@picarro.com
Priority: optional
Version: 0.0.1
Installed-Size: 48 kB
Description: MFG tools for PiGSS
```

```bash
Package: pigss-mfg
Architecture: amd64
Maintainer: gsornsen@picarro.com
Priority: optional
Version: 1.0.0
Installed-Size: 48 kB
Description: MFG tools for PiGSS
```

```bash
Package: pigss-mfg-dev
Architecture: amd64
Maintainer: gsornsen@picarro.com
Priority: optional
Version: 1.0.0
Installed-Size: 48 kB
Description: MFG tools for PiGSS
```
