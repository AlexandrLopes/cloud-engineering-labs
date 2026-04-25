# Stage 1 - Builder
FROM ubuntu:22.04 AS builder

RUN apt-get update && apt-get install -y python3 python3-pip
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --user -r requirements.txt

# Stage 2 - Production  
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y python3
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY app.py .

ENV PATH=/root/.local/bin:$PATH

EXPOSE 8080
CMD ["python3", "app.py"]