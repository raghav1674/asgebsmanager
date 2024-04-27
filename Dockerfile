FROM python:alpine3.19 as builder

WORKDIR /app

COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt 

COPY src  src
COPY setup.py .

RUN python3 setup.py sdist


FROM python:alpine3.19

ENV ASG_EBS_VERSION=1.5.3

WORKDIR /app

COPY --from=builder /app/dist/asgebsmanager-${ASG_EBS_VERSION}.tar.gz  asgebsmanager-${ASG_EBS_VERSION}.tar.gz

RUN python3 -m pip install file:///app/asgebsmanager-${ASG_EBS_VERSION}.tar.gz

ENTRYPOINT ["asgebsmanager"]

CMD ["--help"]




