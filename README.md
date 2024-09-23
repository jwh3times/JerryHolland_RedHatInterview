# Jerry Holland's RedHat Interview

## HTTP FileStore Server and CLI Client

This project consists of an HTTP web server written in Python and a CLI client also written in Python. The Server should be started and remain running as long as desired. It will launch and begin listening on port 5000 for incoming API requests.

The Client should be called with the desired command passed as command arguments. Examples can be found in the following documentation.

## Features

### Adding Files

The filestore supports an 'add' command to place files on the server. This command is designed to specifically add new files and will fail if the file already exists on the filestore. This is to protect files from being overwritten by mistake.

To add a single file to the filestore, the command to execute would look like the following:

#### Linux

```{r, engine='python', count_lines}
python3 client.py add file.txt
```

#### Windows

```{r, engine='python', count_lines}
py client.py add file.txt
```

This command can accept multiple files at once if you wish to do a bulk add to the filestore. To add multiple files at once to the filestore, the command would look like the following:

#### Linux

```{r, engine='python', count_lines}
python3 client.py add file1.txt file2.txt ...
```

#### Windows

```{r, engine='python', count_lines}
py client.py add file1.txt file2.txt ...
```

### Remove Files

The filestore supports an 'rm' command to remove files from the server. This command will accept multiple files just like the add command and remove all specified files from the filestore. Example syntax is as follows.

#### Linux

```{r, engine='python', count_lines}
python3 client.py rm file.txt ...
```

#### Windows

```{r, engine='python', count_lines}
py client.py rm file.txt ...
```

### List Files

The filestore supports an 'ls' command which will return a list of files that exist in the filestore. The returned list of file names will be sorted in alphabetical order.

#### Linux

```{r, engine='python', count_lines}
python3 client.py ls
```

#### Windows

```{r, engine='python', count_lines}
py client.py ls
```

### Update Files

The filestore supports an 'update' command which allows users to update the contents of an existing file in the filestore. This command will also function as an add if the file does not already exist. Like the 'add' and 'rm' commands, this will accept multiple files for updating or adding. The syntax for this command is as follows:

#### Linux

```{r, engine='python', count_lines}
python3 client.py update file.txt ...
```

#### Windows

```{r, engine='python', count_lines}
py client.py update file.txt ...
```

### Get Word Count of Files
The filestore supports a 'wc' command which is used to return the word count of all files currently in the filestore.+
```{r, engine='python', count_lines}
py client.py wc
```

### Get Word Frequency of Files

```{r, engine='python', count_lines}
py client.py freq-words
```

## Requirements

Must have Python 3.12 installed.

### Installation

- pip install -r requirements.txt
- flask --app ./FileStore_Server/src/server run
