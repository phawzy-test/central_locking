FROM ubuntu

MAINTAINER Mohamed Fawzy <mhmd.fawzy.011@gmail.com>

RUN apt-get update -y && apt-get install git python python-pip -y
RUN cd /tmp \
    && git clone https://github.com/phawzy/central_locking.git \
    && cd central_locking \
    && pip install -r requirements.txt

EXPOSE 9191

CMD ["python", "/tmp/central_locking/server.py"]