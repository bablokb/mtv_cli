FROM debian:10-slim

# Prepare image: Update packages, add useradd
RUN apt update && \
    apt upgrade -y && \
    apt install -y wget && \
    useradd -m mtv

# Install mtv_cli
COPY files /install/files
COPY tools /install/tools
RUN /install/tools/install-mtv_cli mtv && \
    rm -rf /var/lib/apt/lists/* /install

# Docker-specific adaptions
RUN mkdir -p /data/db /downloads && \
    mv /etc/mtv_cli.conf /etc/mtv_sendinforc /data/ && \
    sed -i "s/data\/videos/downloads/" /data/mtv_cli.conf && \
    ln -s /data/mtv_cli.conf /etc/mtv_cli.conf && \
    ln -s /data/mtv_sendinforc /etc/mtv_sendinforc && \
    chown mtv /data/db /downloads && \
    ln -s /data/db /home/mtv/.mediathek3
VOLUME /data
VOLUME /downloads
COPY docker/ /
CMD /entrypoint

EXPOSE 8026

USER mtv

