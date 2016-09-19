FROM continuumio/anaconda:latest
MAINTAINER Sze Tan <stan@picarro.com>

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get dist-upgrade -y

RUN apt-get install -y openssh-server
RUN apt-get install -y build-essential
RUN apt-get install -y nano
RUN curl -sL https://deb.nodesource.com/setup_4.x | bash -
RUN apt-get install -y nodejs
RUN apt-get install -y libudev-dev
RUN apt-get install -y usbutils
RUN conda install wxpython
RUN conda install pyserial
RUN pip install subprocess32

RUN mkdir /var/run/sshd
RUN useradd G2000 -m -s /bin/bash
# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

RUN mkdir /home/G2000/resources
WORKDIR /home/G2000/resources
RUN wget -O libusb-1.0.20.tar.bz2 http://sourceforge.net/projects/libusb/files/libusb-1.0/libusb-1.0.20/libusb-1.0.20.tar.bz2/download
RUN tar -xvjf libusb-1.0.20.tar.bz2
WORKDIR /home/G2000/resources/libusb-1.0.20
RUN ./configure
RUN make
RUN make install
RUN ldconfig

WORKDIR /home/G2000/resources
RUN git clone https://github.com/vpelletier/python-libusb1.git
WORKDIR /home/G2000/resources/python-libusb1
RUN python setup.py install
