FROM picarrodocker/host_base:latest
MAINTAINER Sze Tan <stan@picarro.com>

RUN apt-get update
RUN echo 'root:bl52l21fbl52l21f' |chpasswd
RUN sed --in-place=.bak 's/without-password/yes/' /etc/ssh/sshd_config

RUN useradd picarro -m
RUN echo 'picarro:picarro' |chpasswd

COPY Picarro.pth /opt/conda/lib/python2.7/site-packages/Picarro.pth

RUN pip install Pyro4==4.26

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
