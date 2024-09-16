import os
import pathlib
from typing import Annotated, List, Optional
import requests
import json
import typer
import zipfile
from zipfile import ZipFile

host = "http://127.0.0.1:5000"

def main(cmd: Annotated[str, typer.Argument()], 
         args: Annotated[Optional[List[str]], typer.Argument()] = None):
    match cmd:
        case "add":
            saveFiles(args)
        case "ls":
            getFiles()
        case "rm":
            removeFiles(args)
        case "update":
            updateFiles(args)
        case "wc":
            getWordCount()
        case "freq-words":
            getWordFreq()
        case _:
            print(f"Unsupported command: {cmd}")
            print(f"Supported commands are add, ls, rm, update, wc, freq-words")

def saveFiles(args):
    z = ZipFile(file='fs_files.zip', mode='w', compression=zipfile.ZIP_DEFLATED)
    for a in args:
        filePath = str(pathlib.Path(__file__).parent.parent.resolve()) + "\\resources\\" + a
        z.write(filename=filePath, arcname=a)
    z.close()
    f = open('fs_files.zip', 'rb')
    f_dict = {"file": f}
    response = requests.post(url=host+'/files', files=f_dict)
    f.close()
    os.remove('fs_files.zip')
    print(response.text)
    
def getFiles():
    response = requests.get(url=host+'/files')
    print(response.text)
    
def removeFiles(args):
    filenames = ''
    for a in args:
        filenames += f"{a},"
    filenames = filenames[:-1]
    payload = {'filenames': filenames}
    response = requests.delete(url=host+'/files', data=json.dumps(payload))
    print(response.text)
    
def updateFiles(args):
    z = ZipFile(file='fs_files.zip', mode='w', compression=zipfile.ZIP_DEFLATED)
    for a in args:
        filePath = str(pathlib.Path(__file__).parent.parent.resolve()) + "\\resources\\" + a
        z.write(filename=filePath, arcname=a)
    z.close()
    f = open('fs_files.zip', 'rb')
    f_dict = {"file": f}
    response = requests.put(url=host+'/files', files=f_dict)
    print(response.text)
    f.close()
    os.remove('fs_files.zip')
    
def getWordCount():
    response = requests.get(url=host+'/wordcount')
    print(response.text)
    
def getWordFreq():
    response = requests.get(url=host+'/wordfrequency')
    print(response.text)

if __name__ == "__main__":
    typer.run(main)