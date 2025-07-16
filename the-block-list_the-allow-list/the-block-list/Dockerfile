FROM python:3

ENV http_proxy="http://<username>:<password>@<proxy-server>"
ENV https_proxy="http://<username>:<password>@<proxy-server>"

RUN apt-get update && apt-get install -y curl

WORKDIR /worker
COPY . The-Block-List
RUN test ! -e The-Block-List/requirements.txt || pip install --proxy http://<username>:<password>@<proxy-server> --no-cache-dir -r The-Block-List/requirements.txt
ENTRYPOINT The-Block-List/the-block-list.py