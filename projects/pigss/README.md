# PiGSS (Picarro Gas Sample Sequencer) Project

## Setting up the Environment

***

### Operating System

* Download /Install [Ubuntu 18.04.x](https://ubuntu.com/download/desktop)
  * Username: picarro
  * Ensure you have Internet Access
  * Check box for Minimal Install
  * Check box for Automatically Download Updates

***

### Ansible

The operating system will automatically be configured/provisioned by the PiGSS Ansible playbook. We recommend developing in a Virtual Machine if using this playbook for development. The same playbook will be used to provision the BuildAgent in TeamCity, as well as provision the ISO/FOG image we use in production.

There are three variables that must be used with the `--extra-vars` command line argument for the ansible playbook to run properly.

`headless`

* `true` - For TeamCity BuildAgent
* `false` - For Development/Production Environment

`dev`

* `true` - For Non-Production Environment
* `false` - For Production Environment

`update`

* `true` - For Updating an Environment Already Provisioned by Ansible
* `false` For Provisioning a Fresh OS Minimal Install

#### Developer Bash Command

```bash
sudo apt update -y && sudo apt upgrade -y && sudo apt install -y ansible git curl aptitude && curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash - && sudo apt remove nodejs -y && sudo apt install nodejs -y && mkdir git && cd git && git clone -b develop https://github.com/picarro/I2000-Host.git host && ansible-playbook host/projects/pigss/ansible/pigss.yaml --extra-vars "headless=false dev=true update=false" --ask-become-pass
```

#### TeamCity BuildAgent Bash Command

```bash
sudo apt update -y && sudo apt upgrade -y && sudo apt install -y ansible git curl aptitude && curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash - && sudo apt remove nodejs -y && sudo apt install nodejs -y && mkdir git && cd git && git clone -b develop https://github.com/picarro/I2000-Host.git host && ansible-playbook host/projects/pigss/ansible/pigss.yaml --extra-vars "headless=true dev=true update=false" --ask-become-pass
```

#### Production Image Bash Command

```bash
sudo apt update -y && sudo apt upgrade -y && sudo apt install -y ansible git curl aptitude && curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash - && sudo apt remove nodejs -y && sudo apt install nodejs -y && mkdir git && cd git && git clone -b develop https://github.com/picarro/I2000-Host.git host && ansible-playbook host/projects/pigss/ansible/pigss.yaml --extra-vars "headless=false dev=false update=false" --ask-become-pass
```

If you come across the error(s) below, just wait a few minutes for the unattended upgrades to complete and try again

```bash
E: Could not get lock /var/lib/dpkg/lock-frontend - open (11: Resource temporarily unavailable)
E: Unable to acquire the dpkg frontend lock (/var/lib/dpkg/lock-frontend), is another process using it?
```

***

### Updating

Updating a machine that has already provisioned by Ansible is simple with the following command

`headless`

* `true` - For TeamCity BuildAgent
* `false` - For Development/Production Environment

`dev`

* `true` - For Non-Production Environment
* `false` - For Production Environment

```bash
ansible-playbook host/projects/pigss/ansible/pigss.yaml --extra-vars "headless=<bool> dev=<bool> update=true" --ask-become-pass
```
