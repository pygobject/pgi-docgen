FROM debian:testing

ENV LANG C.UTF-8

RUN echo "deb http://debug.mirrors.debian.org/debian-debug/ testing-debug main" >> /etc/apt/sources.list
RUN rm /etc/apt/apt.conf.d/docker-no-languages

RUN apt-get update

RUN apt-get install -y \
    python3 \
    python3-pip \
    git \
    sudo \
    python3-lxml \
    graphviz \
    python3-apt \
    dctrl-tools \
    apt-file \
    xvfb

RUN apt-file update

ARG HOST_USER_ID=5555
ENV HOST_USER_ID ${HOST_USER_ID}
RUN useradd -u $HOST_USER_ID -ms /bin/bash user
RUN echo 'user ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
USER user

ENV PATH="/home/user/.local/bin:${PATH}"

RUN pip3 install --user --upgrade \
    "git+https://github.com/pygobject/pgi.git" \
    requests==2.22.0 \
    jinja2==2.10.1 \
    sphinx==1.8.5 \
    cairocffi==1.0.2 \
    beautifulsoup4==4.7.1 \
    pytest \
    flake8 \
    coverage \
    pytest-cov

WORKDIR /home/user
COPY --chown=user:user . ./install
WORKDIR /home/user/install

ENV PYTHONPATH /home/user/install
RUN ./pgi-docgen create-debian --install --no-build _docs
ENV PGI_DOCGEN_DEBIAN_DATA_DIR /home/user/install/_debian_build_cache

WORKDIR /home/user/app
