FROM public.ecr.aws/amazonlinux/amazonlinux:2023

# install dependencies
RUN dnf -y update \
    && dnf -y install \
    java \
    python3 \
    python3-devel \
    python3-pip \
    python3-setuptools \
    R \
    && dnf clean all

ENV APP_HOME=/server

ENV PYTHONPATH=${APP_HOME}:${PYTHONPATH}

ENV PYTHONUNBUFFERED=1

ENV PORT=9000

ENV TIMEOUT=900

RUN mkdir -p ${APP_HOME}

WORKDIR ${APP_HOME}

COPY server/requirements.txt .

RUN python3 -m pip install -r requirements.txt

COPY server/ .

EXPOSE ${PORT}

CMD gunicorn \
    server:app \
    --workers `nproc` \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT} \
    --enable-stdio-inheritance
