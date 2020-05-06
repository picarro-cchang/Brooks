# SAM - Build and Deploy Process

## Build

### Development

* Open [TeamCity](http://teamcitydev.picarro.int/overview.html)
* Locate following packages
    * pigss-core-dev
    * pigss-grafana
    * pigss-launcher-dev
    * pigss-lologger-dev
    * pigss-mfg-dev
    * pigss-plugins-dev

### Production

...Coming Soon

**Click `Run` to start building the packages**

## Deployment

### Services

Note: Perform following steps only if the deployment is done for the first time.

Check status of following services:

    sudo systemctl is-active grafana-server.service
    sudo systemctl is-active pigss-core.service
    sudo systemctl is-active lologger.service

Disable services using following command

    sudo systemctl disbale "NAME_OF_SERVICE"

Stop the service using following command

    sudo systemctl stop "NAME_OF_SERVICE"

### Download Packages from [Artifactory](https://picarro.jfrog.io/picarro/webapp/#/login)

Install packages:

    sudo apt install ./grafana_VERSION_amd64.deb
    sudo apt install ./pigss-launcher-dev-VERSION.deb
    sudo apt install ./lologger-dev-VERSION.deb
    sudo apt install ./pigss-mfg-dev-VERSION.deb
    sudo apt install ./pigss-plugins-dev-VERSION.deb
    sudo apt install ./pigss-core-dev-VERSION.deb

Note: Untill `pigss-core` systemd service is fixed do following:

    sudo systemctl disable pigss-core.service
    sudo systemctl stop pigss-core.service

## Run

    pigss-core