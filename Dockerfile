FROM python:3.11.1-slim-buster AS builder

LABEL maintainer="Ellis Yu <ellis.yu@thisisrainbow.com>"

EXPOSE 10332

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . /app

RUN apt-get -y update && apt-get -y install curl \
    && mkdir -p /etc/pki/tls/certs \
    && curl https://curl.se/ca/cacert.pem -o /etc/pki/tls/certs/ca-bundle.crt \
    && pip install --upgrade pip \
    && pip install --no-cache-dir pipenv \
    && pipenv install --skip-lock --system

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10332"]

