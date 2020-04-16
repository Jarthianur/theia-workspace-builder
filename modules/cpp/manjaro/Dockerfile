ARG BOOST=no

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
