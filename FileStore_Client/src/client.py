import os
import pathlib
from typing import Annotated, List, Optional
import requests
import json
import typer
import zipfile
from zipfile import ZipFile
import hashlib

serverURL = ""

def main(cmd: Annotated[str, typer.Argument()], 
         args: Annotated[Optional[List[str]], typer.Argument()] = None,
         limit: Annotated[Optional[int], typer.Option("--limit", "-n")] = 10,
         orderBy: Annotated[Optional[str], typer.Option("--order")] = 'dsc',
         host: Annotated[Optional[str], typer.Option("--host")] = 'http://127.0.0.1',
         port: Annotated[Optional[int], typer.Option("--port")] = 5000):
    """
    Excecute the CLI client application. Utilizing any parameters passed in by the user.
    
    :param cmd: the command to execute on the filestore
    :param args: the list of files to execute the command on
    :param limit: limit the responses from the freq-words command
    :param orderBy: sort the freq-words response in asc or dsc order
    :param host: the host url of the server
    :param port: the port that the server is listening on
    """
    global serverURL
    
    # ensure the host has the correct prefix
    if host[:7] != 'http://':
        host = 'http://' + host
        
    serverURL = host + ':' + str(port)
    match cmd:
        case "add":
            saveFiles(args, updateExisting=False)
        case "ls":
            getFiles()
        case "rm":
            removeFiles(args)
        case "update":
            saveFiles(args, updateExisting=True)
        case "wc":
            getWordCount()
        case "freq-words":
            getWordFreq(limit, orderBy)
        case _:
            print(f"Unsupported command: {cmd}")
            print(f"Supported commands are add, ls, rm, update, wc, freq-words")

def saveFiles(args, updateExisting=False):
    """
    Save a new file or Update an existing file in the filestore

    :param args: the args list of files passed into the cli
    :param updateExisting: used to distinguish between add or update command 
    behavior. add will fail if the file exists while update will replace the file
    """
    z = ZipFile(file='fs_files.zip', mode='w', compression=zipfile.ZIP_DEFLATED)
    for a in args:
        # Check if the user passed in a path to a file or just the filename
        if not os.path.isfile(a):
            filePath = str(pathlib.Path(__file__).parent.parent.resolve().joinpath("resources").joinpath(a))
            fileName = a
        else:
            filePath = a
            fileName = pathlib.Path(a).name
        
        # Calculate the sha256 checksum and send a copy dupe request as a potential optimization
        sha256Sum = hashlib.file_digest(open(filePath, 'rb'), 'sha256').hexdigest()
        response = requests.post(url=serverURL+'/copydupe', params={'sha256': sha256Sum, 'fileName': fileName})
        if response.json()['dupeFound'] == False:
            # no dupe found. need to upload the file
            z.write(filename=filePath, arcname=fileName)
        else:
            print(f"File with identical contents found. Optimizing the file save process.")
    z.close()
    f = open('fs_files.zip', 'rb')
    f_dict = {"file": f}
    if updateExisting:
        response = requests.put(url=serverURL+'/files', files=f_dict)
    else:
        response = requests.post(url=serverURL+'/files', files=f_dict)
    f.close()
    os.remove('fs_files.zip')
    print(response)
    print(response.text)
    
def getFiles():
    """
    Get and display a list of files currently in the filestore
    """
    response = requests.get(url=serverURL+'/files')
    print(response)
    print(response.text)
    
def removeFiles(args):
    """
    Remove file(s) from the filestore

    :param args: the args string of files to remove from the cli
    """
    filenames = ''
    for a in args:
        # Check if the user passed in a path to a file or just the filename
        if not os.path.isfile(a):
            filenames += f"{a},"
        else:
            filenames += f"{pathlib.Path(a).name},"
            
    # remove the trailing comma
    filenames = filenames[:-1]
    payload = {'filenames': filenames}
    response = requests.delete(url=serverURL+'/files', data=json.dumps(payload))
    print(response)
    
def getWordCount():
    """
    Get the word count of all files currently in the filestore
    """
    response = requests.get(url=serverURL+'/wordcount')
    print(response)
    print(response.text)
    
def getWordFreq(limit, orderBy):
    """
    Get the frequency of all words in all files combined within the filestore

    :param limit: the numerical limit of how many words to include in the response
    :param orderBy: asc or dsc to indicate ascending or descending sorting
    """
    params = {'limit': limit, 'orderBy': orderBy}
    response = requests.get(url=serverURL+'/wordfrequency', params=params)
    print(response)
    if response.text == "No files currently stored":
        print(response.text)
    else:
        try:
            print(str(response.json())[1:-1].replace('[', '').replace('], ', '\r\n')[:-1].replace(',', ' ='))
        except json.JSONDecodeError as e:
            print("Error decoding server response")

if __name__ == "__main__":
    typer.run(main)