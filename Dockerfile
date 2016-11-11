# Quickstart:
# docker build -t stepler-tests .
# docker run --net=host --rm \
#    -e OS_AUTH_URL=http://10.109.13.10:5000/v3 \
#    -v $(pwd):/opt/app/test_reports
#    stepler stepler/nova
#
# To run on cloud with ssl change `docker run` to `docker --dns=<cloud dns ip> run`

FROM python:2

RUN  apt-get update -qq &&  \
apt-get install -q -y \
    python-dev \
    libvirt-dev \
    xvfb \
    iceweasel \
    libav-tools && \
apt-get clean  && \
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /opt/app

COPY requirements.txt /opt/app
COPY c-requirements.txt /opt/app
RUN pip install -r requirements.txt -r c-requirements.txt

COPY . /opt/app

ENV OS_USERNAME=admin
ENV OS_PASSWORD=admin
ENV VIRTUAL_DISPLAY=1

ENTRYPOINT ["py.test", "-v", "--junit-xml=test_reports/report.xml"]
