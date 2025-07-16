FROM python:3

ENV http_proxy="http://<username>:<password>@<proxy-server>"
ENV https_proxy="http://<username>:<password>@<proxy-server>"

RUN apt-get update && apt-get install -y curl

WORKDIR /worker
COPY . The-Allow-List
RUN test ! -e The-Allow-List/requirements.txt || pip install --proxy http://<username>:<password>@<proxy-server> --no-cache-dir -r The-Allow-List/requirements.txt
ENTRYPOINT The-Allow-List/the-allow-list.py