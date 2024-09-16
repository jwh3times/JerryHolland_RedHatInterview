import os
from flask import Flask, flash, jsonify, request
import pathlib
import zipfile
from zipfile import ZipFile
import json

UPLOAD_FOLDER = str(pathlib.Path(__file__).parent.parent.resolve()) + "\\resources\\filestore\\"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def root():
    return app.redirect("/health")

@app.route("/health")
def health_check():
    return "Server is healthy!"

@app.route("/files", methods=["POST","GET","DELETE","PUT"])
def serviceFiles():
    if request.method == "POST":
        return saveFiles(request, False)
    elif request.method == "GET":
        return getFiles()
    elif request.method == "DELETE":
        return deleteFiles(request)
    elif request.method == "PUT":
        return saveFiles(request, True)
    else:
        return f"Unknown command: {request.method}"

@app.route("/wordcount", methods=["GET"])
def wordcount():
    return getWordCount()

@app.route("/wordfrequency", methods=["GET"])
def wordfrequency():
    orderBy = request.args.get('orderBy', default='ASC', type=str)
    limit = request.args.get('limit', default=10, type=int)
    return getWordFreq()
    
def saveFiles(request, update):
    zipped = request.files['file']
    try:
        z = ZipFile(file=zipped, mode='r', compression=zipfile.ZIP_DEFLATED, metadata_encoding='utf-8')
    except:
        return "ERROR: Unable to create ZipFile object"
    
    if not update:
        try:
            for f in z.filelist:
                if pathlib.Path(os.path.join(app.config['UPLOAD_FOLDER']) + f.filename).is_file():
                    raise FileExistsError(f"{f.filename} already exists")
        except FileExistsError:
            return f"ERROR: {f.filename} already exists"
    
    try:
        ZipFile.extractall(z, os.path.join(app.config['UPLOAD_FOLDER']))
    except:
        return "ERROR: Unable to extract files to save"
    return "Files Saved"

def getFiles():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return files

def deleteFiles(request):
    json_filenames = json.loads(request.data.decode('utf-8'))
    filenames_str = json_filenames['filenames']
    filenames = str.split(filenames_str, ',')
    for f in filenames:
        os.remove(app.config['UPLOAD_FOLDER'] + f)
    return "deleted files"

def getWordCount():
    files = getFiles()
    result = ""
    if (len(files) == 0):
        return "No files currently stored"
    for file in files:
        f = open(app.config['UPLOAD_FOLDER'] + file, "rt")
        words = [word for line in f for word in line.rstrip().split()]
        result += f"{file} wordcount = {len(words)}\n"
    return result[:-1]

def myKey(t):
    return t[1],t[0]

def getWordFreq():
    files = getFiles()
    word_dict = {}
    if (len(files) == 0):
        return "No files currently stored"
    for file in files:
        f = open(app.config['UPLOAD_FOLDER'] + file, "rt")
        words = [word for line in f for word in line.rstrip().split()]
        for word in words:
            if word[-1] == '.':
                word = word[:-1]
            word_dict.update({word: (word_dict.get(word) + 1) if word_dict.get(word) else 1})
    print(word_dict)
    word_list = sorted(word_dict.items(), key=myKey, reverse=False)
    return word_list