FROM ubuntu:16.04


RUN apt-get update -y &&  apt-get install -y software-properties-common && add-apt-repository ppa:deadsnakes/ppa && apt-get update &&\
apt-get -y  install python3.7 python3-pip python3.7-dev build-essential libssl-dev libffi-dev

# We copy just the requirements.txt first to leverage Docker cache
#COPY ./requirements.txt /app/requirements.txt
RUN useradd -ms /bin/bash newuser
USER newuser
WORKDIR /home/newuser
#RUN pip install -r requirements.txt

COPY requirements.txt .
RUN pip3 install -r requirements.txt


EXPOSE 8000
COPY  . .
RUN ls .

#ENTRYPOINT [ "python3 application.py" ]

#CMD [ "app.py" ]