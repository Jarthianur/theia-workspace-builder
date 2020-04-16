FROM manjarolinux/base:latest

ARG THEIA_UID=1337

RUN pacman -Syyuu --noconfirm && \
    pacman -S --noconfirm yarn nvm tar grep awk wget git make python2 sudo && \
    pacman -Scc --noconfirm

RUN pacman -S --noconfirm \
      clang \
      openmp \
      openmpi \
      gcc \
      cmake \
      make \
      gdb \
      binutils \
      boost \
      boost-libs && \
    pacman -Scc --noconfirm

RUN useradd -s /bin/bash -m -d /home/theia -U -u $THEIA_UID -c '' theia && \
    chmod g+rw /home && \
    mkdir -p /home/project && \
    chown -R theia:theia /home/theia && \
    chown -R theia:theia /home/project && \
    echo 'theia ALL = NOPASSWD: /usr/bin/pacman' >> /etc/sudoers

USER theia
WORKDIR /home/theia
ADD package.json ./package.json
ADD settings.json /home/theia/.theia/

RUN source /usr/share/nvm/init-nvm.sh && \
    nvm install 10 && \
    nvm use 10 && \
    mkdir bin && \
    ln -s "$(echo -n $PATH | tr ':' '\n' | grep nvm)/node" /home/theia/bin/node && \
    ln -s /usr/bin/python2 /home/theia/bin/python

ENV PATH=/home/theia/bin:$PATH

RUN source /usr/share/nvm/init-nvm.sh && \
    yarn --pure-lockfile && \
    NODE_OPTIONS="--max_old_space_size=4096" yarn theia build && \
    yarn theia download:plugins && \
    yarn --production && \
    yarn autoclean --init && \
    echo *.ts >> .yarnclean && \
    echo *.ts.map >> .yarnclean && \
    echo *.spec.* >> .yarnclean && \
    yarn autoclean --force && \
    yarn cache clean

ENV THEIA_DEFAULT_PLUGINS=local-dir:/home/theia/plugins \
    SHELL=/bin/bash

EXPOSE 3000

ENTRYPOINT [ "node", "/home/theia/src-gen/backend/main.js", "/home/project", "--hostname=0.0.0.0" ]