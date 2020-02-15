FROM python:3.7-buster
# Access token for the gitlab user
ENV GL_ACCESS_TOKEN=abcdefghijklmnopqrstuvwxyz
# Config file to use
ENV NP_CONFIG_FILE=/opt/nittymcpick/config.json
# URL of the Gitlab server
ENV GITLAB_SERVER=http://127.0.0.1
# Username @ GitLab
ENV GITLAB_USER=nittymcpick
# Bind to... 
ENV NP_HOST=0.0.0.0
# ..on port
ENV NP_PORT=8888
# Additional arguments
ENV NP_ADDARGUMENT="--nowip --onlynew"

RUN useradd -U -m -s /bin/sh nittymcpick && \
    mkdir -p /opt/nittymcpick && \
    chown -R nittymcpick:nittymcpick /opt/nittymcpick && \
    adduser nittymcpick root && \
    pip3 install nittymcpick

USER nittymcpick
WORKDIR /opt/nittymcpick
CMD ["/bin/sh", "-c", "nittymcpick ${NP_ADDARGUMENT} --host=${NP_HOST} --port=${NP_PORT} ${GITLAB_SERVER} ${GITLAB_USER} ${NP_CONFIG_FILE}"]
ENTRYPOINT ["/bin/sh"]
