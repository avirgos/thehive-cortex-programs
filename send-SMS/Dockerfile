FROM python:alpine

RUN apk update && \
    apk add --no-cache perl perl-dev build-base && \
    apk add --no-cache curl && \
    curl -L https://cpanmin.us | perl - App::cpanminus && \
    cpanm --force LWP::Simple

WORKDIR /worker
COPY . Send-SMS

RUN pip install --root-user-action=ignore --upgrade pip

RUN test ! -e Send-SMS/requirements.txt || pip install --root-user-action=ignore --no-cache-dir -r Send-SMS/requirements.txt

ENTRYPOINT Send-SMS/send-SMS.py