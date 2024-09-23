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
COPY . .

# run the flask server  
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]