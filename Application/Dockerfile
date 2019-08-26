# FROM ubuntu:16.04


# RUN apt-get update -y &&  apt-get install -y software-properties-common && add-apt-repository ppa:deadsnakes/ppa && apt-get update &&\
# apt-get -y  install python3.7 python3-pip python3.7-dev build-essential  
FROM ubuntu:16.04

RUN apt-get update && \
        apt-get install -y software-properties-common  &&\
        add-apt-repository ppa:deadsnakes/ppa

RUN apt-get update -y

RUN apt-get install -y build-essential python3.7 python3.7-dev python3-pip python3.7-venv && \
        apt-get install -y libssl-dev libffi-dev

# update pip
RUN python3.7 -m pip install pip --upgrade && \
        python3.7 -m pip install wheel

# RUN useradd -ms /bin/bash newuser
# USER newuser
# WORKDIR /home/newuser
#RUN apt-get install -y python2.7 python2.7-dev python-pip
# We copy just the requirements.txt first to leverage Docker cache
#COPY ./requirements.txt /app/requirements.txt
# RUN useradd -ms /bin/bash newuser
# USER newuser
# WORKDIR /home/newuser
#RUN pip install -r requirements.txt

#RUN python3.7 -m pip install pip --upgrade
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY  . .
RUN ls .
EXPOSE 8000

RUN pyi-makespec -F --hidden-import engineio.async_eventlet \
 --hidden-import _striptime --hidden-import engineio.async_gevent \
 --additional-hooks-dir pyinstaller_hooks --onefile --windowed \
 --icon datapod.ico --name Datapod_ubuntu  application.py
RUN pyinstaller Datapod_ubuntu.spec --distpath releases/



#ENTRYPOINT [ "python3 application.py" ]

#CMD [ "app.py" ]