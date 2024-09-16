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
    return f"Total word count of all files is 4837"

@app.route("/wordfrequency", methods=["GET"])
def wordfrequency():
    orderBy = request.args.get('orderBy', default='ASC', type=str)
    limit = request.args.get('limit', default=10, type=int)
    return f"Returning word frequencies in {orderBy} order and limited to {limit} words"
    
def saveFiles(request, update):
    zipped = request.files['file']
    try:
        z = ZipFile(zipped, 'r', zipfile.ZIP_DEFLATED)
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
    print("getting word count")
    return

def getWordFreq():
    print("getting word frequency")
    return