FROM picarrodocker/host_base:latest
MAINTAINER Sze Tan <stan@picarro.com>


RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get dist-upgrade -y

RUN apt-get install -y fuse
RUN pip install Pyro4
RUN pip install fusepy

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y lxde terminator
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y tightvncserver
RUN rm -rf /var/lib/apt/lists/*

RUN apt-get update -y

# Libraries for VSCode
RUN apt-get install -y libnspr4 libnss3
# Patch (see https://github.com/Microsoft/vscode/issues/3451)
WORKDIR /usr/lib/x86_64-linux-gnu/
RUN cp libxcb.so.1 libxcb.so.1.orig
RUN sed -i 's/BIG-REQUESTS/_IG-REQUESTS/' /usr/lib/x86_64-linux-gnu/libxcb.so.1
# Install VSCode
WORKDIR /home/G2000/resources
RUN wget -O code.deb https://go.microsoft.com/fwlink/?LinkID=760868
RUN dpkg -i code.deb

RUN echo 'root:bl52l21fbl52l21f' |chpasswd
RUN sed --in-place=.bak 's/without-password/yes/' /etc/ssh/sshd_config

RUN useradd picarro -m -s /bin/bash
RUN echo 'picarro:picarro' |chpasswd

COPY Picarro.pth /opt/conda/lib/python2.7/site-packages/Picarro.pth
# Make a mount point for the FUSE based logger
RUN mkdir /mnt/applog


# VNC directories and files
RUN mkdir /home/picarro/.vnc
RUN mkdir /home/G2000/.vnc
RUN mkdir /root/.vnc

RUN echo 12345 | vncpasswd -f > /home/picarro/.vnc/passwd
RUN chmod 600 /home/picarro/.vnc/passwd

COPY xstartup /home/picarro/.vnc/xstartup
RUN chmod 755 /home/picarro/.vnc/xstartup
COPY xstartup /home/G2000/.vnc/xstartup
RUN chmod 755 /home/G2000/.vnc/xstartup
COPY xstartup /root/.vnc/xstartup
RUN chmod 755 /root/.vnc/xstartup

RUN chown -R picarro.picarro /home/picarro/.vnc
RUN chown -R G2000.G2000 /home/G2000/.vnc

COPY setup-start /usr/bin

WORKDIR /home/picarro
# Set up path to Anaconda Python
ENV PATH /opt/conda/bin:$PATH
CMD ["/usr/bin/setup-start"]

EXPOSE 22 5901 40000
