# Build Grafana

## Run Tests

```bash
make test
```

This will run the front-end and back-end tests for our custom [Grafana](https://github.com/picarro/grafana) -- However Grafana's own tests do not pass in the current state.

***

## Local Build

```bash
make deb
```

`grafana_<version>-<epoch>.deb` will be placed in the `dist` folder

The epoch timestamp will be generated during the build

The version can be found in `package.json`

```json
{
  "author": "Grafana Labs",
  "license": "Apache-2.0",
  "private": true,
  "name": "grafana",
  "version": "6.4.2",
  "repository": {
    "type": "git",
    "url": "http://github.com/grafana/grafana.git"}
}
```

Example Filename: `grafana_6.4.2-1571619165_amd64.deb`

***

## CI/CD Integration

Currently, we'll use the same command as local builds to build Grafana. In the future, when we work out tests, we can enable hooks to run the tests, and auto-increment the revision number in `package.json`

For now, we'll have to be deliberate when making testing/production builds by manually changing the revision number in `package.json`, committing/pushing, and manually triggering the build inside of TeamCity.

The major and minor numbers shall always reflect the version of Grafana we are customizing in our repo. These do not ever get changed by us. They will be provided automatically when we create a topic branch off of the official Grafana branch we would like to build from or do a pull from upstream to get those sweet new features.

### Examples

```bash
make deb
```

`grafana_<version>-<epoch>.deb` will be placed in the `dist` folder

The epoch timestamp will be generated during the build

The version can be found in `package.json`

```json
{
  "author": "Grafana Labs",
  "license": "Apache-2.0",
  "private": true,
  "name": "grafana",
  "version": "6.4.2",
  "repository": {
    "type": "git",
    "url": "http://github.com/grafana/grafana.git"}
}
```

Example Filename: `grafana_6.4.2-1571619165_amd64.deb`
