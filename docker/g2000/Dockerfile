FROM picarrodocker/host_base:latest
MAINTAINER Sze Tan <stan@picarro.com>

RUN apt-get update

RUN apt-get install -y fuse
RUN pip install Pyro4
RUN pip install fusepy

RUN echo 'root:bl52l21fbl52l21f' |chpasswd
RUN sed --in-place=.bak 's/without-password/yes/' /etc/ssh/sshd_config

RUN useradd picarro -m
RUN echo 'picarro:picarro' |chpasswd

COPY Picarro.pth /opt/conda/lib/python2.7/site-packages/Picarro.pth
COPY rc.local /etc/rc.local
RUN chmod 755 /etc/rc.local
RUN mkdir /mnt/applog

EXPOSE 22
CMD /etc/rc.local && /usr/sbin/sshd -D