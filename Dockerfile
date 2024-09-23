# syntax=docker/dockerfile:1

# base python image for custom image
FROM python:3.12.6

# Add maintainer info
LABEL maintainer="jerryholland00@gmail.com"
LABEL version="0.1.0"

# create working directory and install pip dependencies
WORKDIR /jerry_holland_interview_server
COPY requirements.txt requirements.txt
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

# copy python project files from local to /jerry_holland_interview image working directory
COPY ./FileStore_Server ./

# run the flask server
EXPOSE 5000
CMD [ "flask", "--app", "src/server.py", "run", "--host=0.0.0.0", "--port=5000"]