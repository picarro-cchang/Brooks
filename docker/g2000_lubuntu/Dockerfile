# This produces g2000_lubuntu from host_lubuntu by adding
#  Picarro specific utilities, libraries etc.
#  DO NOT PUSH TO DOCKERHUB

FROM picarrodocker/host_lubuntu:latest
MAINTAINER Sze Tan <stan@picarro.com>

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get dist-upgrade -y

RUN apt-get install -y fuse
RUN apt-get install -y gfortran
RUN pip install Pyro4
RUN pip install fusepy
RUN pip install pyscreenshot
RUN pip install traits
RUN pip install traitsui

# Winpdb latest version (conda version for linux-64 is out of date)
WORKDIR /home/G2000/resources
RUN wget -O winpdb-1.4.8.tar.gz https://storage.googleapis.com/google-code-archive-downloads/v2/code.google.com/winpdb/winpdb-1.4.8.tar.gz
RUN tar -xzf winpdb-1.4.8.tar.gz
WORKDIR /home/G2000/resources/winpdb-1.4.8
RUN python setup.py install -f
RUN apt-get update -y
RUN apt-get install -y xterm

# Libraries for VSCode
RUN apt-get install -y libnspr4 libnss3
# Patch (see https://github.com/Microsoft/vscode/issues/3451)
RUN mkdir /root/lib
RUN cp /usr/lib/x86_64-linux-gnu/libxcb.so.1 /root/lib/libxcb.so.1
RUN sed -i 's/BIG-REQUESTS/_IG-REQUESTS/' /root/lib/libxcb.so.1
RUN apt-get update -y
# Install VSCode
WORKDIR /home/G2000/resources
RUN wget -O code.deb https://go.microsoft.com/fwlink/?LinkID=760868
RUN dpkg -i code.deb
RUN conda install flake8

# Install other 3rd party tools
RUN apt-get install -y meld
RUN apt-get install -y vitables

# Install desktop icons
COPY install_desktop_icon.py /home/G2000/resources
WORKDIR /home/G2000/resources
RUN python install_desktop_icon.py

RUN echo 'root:bl52l21fbl52l21f' |chpasswd
RUN sed --in-place=.bak 's/without-password/yes/' /etc/ssh/sshd_config

RUN useradd picarro -m -s /bin/bash
RUN echo 'picarro:picarro' |chpasswd

COPY Picarro.pth /opt/conda/lib/python2.7/site-packages/Picarro.pth
# Make a mount point for the FUSE based logger
RUN mkdir /mnt/applog

# VNC directories and files
RUN apt-get install -y autocutsel
RUN mkdir /root/.vnc
RUN echo 12345 | vncpasswd -f > /root/.vnc/passwd
RUN chmod 600 /root/.vnc/passwd
COPY xstartup /root/.vnc/xstartup
RUN chmod 755 /root/.vnc/xstartup

COPY setup-start /usr/bin

# Copy code.desktop file to use modified libxcb.so library
RUN mkdir -p /root/.local/share/applications
COPY code.desktop /root/.local/share/applications/code.desktop

WORKDIR /root
# Set up path to Anaconda Python
ENV PATH /opt/conda/bin:$PATH
CMD ["/usr/bin/setup-start"]

EXPOSE 22 5901 40000
