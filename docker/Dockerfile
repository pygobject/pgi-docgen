FROM debian:testing

ENV LANG C.UTF-8

RUN echo "deb http://debug.mirrors.debian.org/debian-debug/ testing-debug main" >> /etc/apt/sources.list
RUN rm /etc/apt/apt.conf.d/docker-no-languages

RUN apt-get update

RUN apt-get install -y \
    python3 \
    git \
    sudo \
    graphviz \
    python3-apt \
    dctrl-tools \
    apt-file \
    xvfb \
    libgirepository-1.0 \
    gir1.2-glib-2.0 \
    pipx

RUN apt-file update

ARG HOST_USER_ID=5555
ENV HOST_USER_ID ${HOST_USER_ID}
RUN useradd -u $HOST_USER_ID -ms /bin/bash user
RUN echo 'user ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
USER user

ENV PATH="/home/user/.local/bin:${PATH}"

WORKDIR /home/user
COPY --chown=user:user . ./app
WORKDIR /home/user/app

RUN pipx install poetry
RUN pipx install --editable --system-site-packages .

RUN pgi-docgen create-debian --cachedir /home/user/_debian_build_cache --install --no-build _docs
