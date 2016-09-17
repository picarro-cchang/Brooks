FROM picarrodocker/host_base:latest
MAINTAINER Sze Tan <stan@picarro.com>


RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get dist-upgrade -y
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y lxde
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y tightvncserver
RUN rm -rf /var/lib/apt/lists/*

RUN apt-get install -y fuse
RUN pip install Pyro4
RUN pip install fusepy

COPY setup-start /usr/bin
COPY home/ /data/home

RUN echo 'root:bl52l21fbl52l21f' |chpasswd
RUN sed --in-place=.bak 's/without-password/yes/' /etc/ssh/sshd_config

RUN useradd picarro -m
RUN echo 'picarro:picarro' |chpasswd

COPY Picarro.pth /opt/conda/lib/python2.7/site-packages/Picarro.pth
COPY rc.local /etc/rc.local
RUN chmod 755 /etc/rc.local
RUN mkdir /mnt/applog

EXPOSE 22 5901 40000
CMD /etc/rc.local && /usr/sbin/sshd -D && setup-start

