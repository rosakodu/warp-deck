FROM ghcr.io/steamdeckhomebrew/holo-base:latest

RUN pacman -Sy --noconfirm && \
    pacman -S --noconfirm go git base-devel libmnl && \
    pacman -Scc --noconfirm

RUN git clone --depth 1 https://github.com/amnezia-vpn/amneziawg-go.git /tmp/amneziawg-go && \
    make -C /tmp/amneziawg-go

RUN git clone --depth 1 https://github.com/amnezia-vpn/amneziawg-tools.git /tmp/amneziawg-tools && \
    make -C /tmp/amneziawg-tools/src

RUN mkdir /binaries && \
    cp /tmp/amneziawg-go/amneziawg-go /binaries/ && \
    cp /tmp/amneziawg-tools/src/wg /binaries/awg
