FROM ubuntu:bionic

ENV LANG C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV CI true

RUN apt-get update && apt-get install -y \
    virtualenv \
    git \
    python3.6-dev \
    python3-venv \
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
    gir1.2-ges-1.0 \
    && rm -rf /var/lib/apt/lists/*
