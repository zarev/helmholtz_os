FROM node:20-bullseye

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        python3 \
        pkg-config \
        libx11-6 \
        libx11-dev \
        libxrandr2 \
        libxrandr-dev \
        libxtst6 \
        libxtst-dev \
        libxinerama1 \
        libxinerama-dev \
        libxcursor1 \
        libxcursor-dev \
        libxi6 \
        libxi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g computer-use-mcp

COPY docker/computer-use-mcp/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

CMD ["/usr/local/bin/entrypoint.sh"]
