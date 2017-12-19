FROM ubuntu:zesty

ENV LANG C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV CI true

RUN apt-get update
RUN apt-get install -y dirmngr
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F23C5A6CF475977595C89F51BA6932366A755776
RUN echo "deb http://ppa.launchpad.net/deadsnakes/ppa/ubuntu xenial main" >> /etc/apt/sources.list
RUN apt-get update

RUN apt-get install -y \
    virtualenv \
    git \
    python2.7-dev \
    python3.4-dev \
    python3.5-dev \
    python3.6-dev \
    dbus \
    xauth \
    xvfb \
    locales \
    libglib2.0-dev \
    libgirepository1.0-dev \
    libatk1.0-dev \
    libpango1.0-dev \
    libgudev-1.0-dev \
    libgtk-3-dev \
    libsoup2.4-dev \
    libgstreamer-plugins-base1.0-dev \
    libgstreamer1.0-dev \
    libges-1.0-dev \
    gir1.2-ges-1.0
