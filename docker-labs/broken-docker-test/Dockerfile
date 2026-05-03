FROM ubuntu:22.04

WORKDIR /app

COPY app.py .

RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip && rm -rf /var/lib/apt/lists/* && pip3 install flask

EXPOSE 1234

CMD ["python3", "app.py"]
