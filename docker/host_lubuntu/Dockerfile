# This produces host_lubuntu from host_base by adding lxde and tightvncserver
FROM picarrodocker/host_base:latest
MAINTAINER Sze Tan <stan@picarro.com>

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get dist-upgrade -y

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y lxde terminator
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y tightvncserver
RUN rm -rf /var/lib/apt/lists/*
