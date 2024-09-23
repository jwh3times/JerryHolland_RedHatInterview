# Jerry Holland's RedHat Interview

## HTTP FileStore Server and CLI Client

This project consists of an HTTP web server written in Python and a CLI client also written in Python. The Server will startup and begin listening on port 5000 for incoming API requests and remain running until stopped by the user.

The Client should be called with the desired command passed as command arguments. Examples can be found in the following documentation.

## Features

### Adding Files

The filestore supports an 'add' command to place files on the server. This command is designed to specifically add new files and will fail if the file already exists on the filestore. This is to protect files from being overwritten by mistake.

To add a single file to the filestore, the command to execute would look like the following:

##### Linux

```
python3 client.py add file.txt
```

##### Windows

```
py client.py add file.txt
```

This command can accept multiple files at once if you wish to do a bulk add to the filestore. To add multiple files at once to the filestore, the command would look like the following:

##### Linux

```
python3 client.py add file1.txt file2.txt ...
```

##### Windows

```
py client.py add file1.txt file2.txt ...
```

### Remove Files

The filestore supports an 'rm' command to remove files from the server. This command will accept multiple files just like the add command and remove all specified files from the filestore. Example syntax is as follows.

##### Linux

```
python3 client.py rm file.txt ...
```

##### Windows

```
py client.py rm file.txt ...
```

### List Files

The filestore supports an 'ls' command which will return a list of files that exist in the filestore. The returned list of file names will be sorted in alphabetical order.

##### Linux

```
python3 client.py ls
```

##### Windows

```
py client.py ls
```

### Update Files

The filestore supports an 'update' command which allows users to update the contents of an existing file in the filestore. This command will also function as an add if the file does not already exist. Like the 'add' and 'rm' commands, this will accept multiple files for updating or adding. The syntax for this command is as follows:

##### Linux

```
python3 client.py update file.txt ...
```

##### Windows

```
py client.py update file.txt ...
```

### Get Word Count of Files

The filestore supports a 'wc' command which is used to return the word count of all files currently in the filestore. The syntax for this command is as follows:

##### Linux

```
python3 client.py wc
```

##### Windows

```
py client.py wc
```

### Get Frequency of Words in Files

The filestore supports a 'freq-words' command which is used to retrieve a list of words and their number of appearances within all files combined in the filestore. The default behavior of this command is to return the top 10 most used words in all files combined. This can be executed using the syntax shown here:

##### Linux

```
python3 client.py freq-words
```

##### Windows

```
py client.py freq-words
```

This command has optional parameters to either change the number of returned values or change the sorting order to be ascending or descending. This can be configured using the syntax shown below:

##### Linux

```
python3 client.py freq-words --limit [number] --order [asc | dsc]
```

##### Windows

```
py client.py freq-words --limit [number] --order [asc | dsc]
```

## Requirements

Must have Python 3.12 installed. If you do not have Python installed or are not sure, following the instructions found here: https://wiki.python.org/moin/BeginnersGuide/Download

## Running the FileStore

### Running the Server locally

Open a terminal session and navigate to the root directory of the repository and run the following command:

```
flask --app ./FileStore_Server/src/server run
```

This will launch the FileStore server on its default port 5000. If you run into issues with this port or wish to specify a different port that can be done as such:

```
flask --app ./FileStore_Server/src/server run --port [number]
```

### Running the Server in Docker

#### Getting the Docker Image

If you wish to run the server in Docker, then you may choose to pull the latest Docker image from my DockerHub using this command:

```
docker pull jwh3times/filestore-server
```

Or, the Dockerfile is included and you may choose to build your own Docker image using this command from the root directory of the repository:

```
docker build -t [username]/filestore-server .
```

#### Running the Docker Image

Then to start a container with this newly created image, run the following command (inserting your desired port number in the annotated location):

```
docker run -d -p [port]:5000 [username]/filestore-server
```

### Deploying the Server in Kubernetes

If you wish to deploy the server in a kubernetes cluster you may do so by executing the following commands:

```
kubectl create -f .\manifest.yaml
kubectl expose deployment jerryholland-filestore-server-deployment --type NodePort --port 5000
```

This will create a service in kubernetes to run replicas of the filestore server. Once the pods are up and running you may run the client CLI and pass the necessary host and port information to access the cluster as shown here:

##### Linux

```
python3 client.py ls --host [host] --port [port]
```

##### Windows

```
py client.py ls --host [host] --port [port]
```

### Running the Client CLI

The client CLI application will pull files from the /FileStore_Client/resources/ directory by default. Meaning if your files are located here then you need only pass in the filename for the app to function correctly. If you wish to upload files located elsewhere then a full filepath would need to be passed in the arguments.

With the Server listening on its default port 5000 then there is no need to specify the port to the client CLI application. You may begin executing commands as shown here:

##### Linux

```
python3 client.py [command] [args]
```

##### Windows

```
py client.py [command] [args]
```

If the server is listening on a port other than its default value then the port will need to be passed to the client CLI application as shown here:

##### Linux

```
python3 client.py [command] [args] --port [number]
```

##### Windows

```
py client.py [command] [args] --port [number]
```
