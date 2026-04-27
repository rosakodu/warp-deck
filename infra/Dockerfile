FROM ghcr.io/steamdeckhomebrew/holo-base:latest

RUN pacman -Sy --noconfirm && \
    pacman -S --noconfirm go git base-devel libmnl && \
    pacman -Scc --noconfirm

ARG AMNEZIAWG_GO_REF=v0.2.17
ARG AMNEZIAWG_TOOLS_REF=v1.0.20260223

RUN git clone --depth 1 --branch "${AMNEZIAWG_GO_REF}" https://github.com/amnezia-vpn/amneziawg-go.git /tmp/amneziawg-go && \
    make -C /tmp/amneziawg-go

RUN git clone --depth 1 --branch "${AMNEZIAWG_TOOLS_REF}" https://github.com/amnezia-vpn/amneziawg-tools.git /tmp/amneziawg-tools && \
    make -C /tmp/amneziawg-tools/src

RUN mkdir /binaries && \
    cp /tmp/amneziawg-go/amneziawg-go /binaries/ && \
    cp /tmp/amneziawg-tools/src/wg /binaries/awg
