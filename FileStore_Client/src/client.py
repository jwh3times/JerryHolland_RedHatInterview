import os
import pathlib
from typing import Annotated, List, Optional
import requests
import json
import typer
import zipfile
from zipfile import ZipFile
import hashlib

serverURL = "http://127.0.0.1:"

def main(cmd: Annotated[str, typer.Argument()], 
         args: Annotated[Optional[List[str]], typer.Argument()] = None,
         limit: Annotated[Optional[int], typer.Option("--limit", "-n")] = None,
         orderBy: Annotated[Optional[str], typer.Option("--order")] = None,
         port: Annotated[Optional[int], typer.Option("--port")] = 5000):
    global serverURL
    serverURL += str(port)
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
    z = ZipFile(file='fs_files.zip', mode='w', compression=zipfile.ZIP_DEFLATED)
    for a in args:
        filePath = str(pathlib.Path(__file__).parent.parent.resolve()) + "\\resources\\" + a
        sha256Sum = hashlib.file_digest(open(filePath, 'rb'), 'sha256').hexdigest()
        response = requests.get(url=serverURL+'/checkdupe', params={'sha256': sha256Sum, 'fileName': a})
        if response.json()['dupeFound'] == False:
            z.write(filename=filePath, arcname=a)
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
    response = requests.get(url=serverURL+'/files')
    print(response)
    print(response.text)
    
def removeFiles(args):
    filenames = ''
    for a in args:
        filenames += f"{a},"
    filenames = filenames[:-1]
    payload = {'filenames': filenames}
    response = requests.delete(url=serverURL+'/files', data=json.dumps(payload))
    print(response)
    
def getWordCount():
    response = requests.get(url=serverURL+'/wordcount')
    print(response)
    print(response.text)
    
def getWordFreq(limit, orderBy):
    params = {'limit': limit, 'orderBy': orderBy}
    response = requests.get(url=serverURL+'/wordfrequency', params=params)
    print(response)
    print(str(response.json())[1:-1].replace('[', '').replace('], ', '\r\n')[:-1].replace(',', ' ='))

if __name__ == "__main__":
    typer.run(main)