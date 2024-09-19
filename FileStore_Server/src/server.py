import hashlib
import os
from typing import Dict, List
from flask import Flask, jsonify, request
import pathlib
import zipfile
from zipfile import ZipFile
import json
import shutil

UPLOAD_FOLDER = str(pathlib.Path(__file__).parent.parent.resolve()) + "\\resources\\filestore\\"
FILE_SUMS_LOC = UPLOAD_FOLDER + "fileSums.json"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['FILE_SUMS_LOC'] = FILE_SUMS_LOC

@app.route("/")
def root():
    return app.redirect("/health")

@app.route("/health")
def health_check():
    return "Server is healthy!"

@app.route("/files", methods=["POST","GET","DELETE","PUT"])
def serviceFiles():
    if request.method == "POST":
        return saveFiles(request, update=False)
    elif request.method == "GET":
        return getFiles()
    elif request.method == "DELETE":
        return jsonify({'Success': deleteFiles(request)}), 204
    elif request.method == "PUT":
        return saveFiles(request, update=True)
    else:
        return f"Unknown command: {request.method}"

@app.route("/wordcount", methods=["GET"])
def wordcount():
    return getWordCount()

@app.route("/wordfrequency", methods=["GET"])
def wordfrequency():
    orderBy = request.args.get('orderBy', default='ASC', type=str)
    limit = request.args.get('limit', default=10, type=int)
    return getWordFreq(limit, orderBy)

@app.route("/checkdupe", methods=["GET"])
def getCheckDupe():
    csum =  request.args.get('sha256', type=str)
    fn = request.args.get('fileName', type=str)
    dupeFile = findDupeFile(csum, fn) or False
    if dupeFile and dupeFile != fn:
        shutil.copyfile(os.path.join(app.config['UPLOAD_FOLDER']) + dupeFile, os.path.join(app.config['UPLOAD_FOLDER']) + fn)
        with open(os.path.join(app.config['FILE_SUMS_LOC']), 'r+', encoding='utf-8') as f:
            existing = json.load(f)
        remove_fileName_from_checkSums(fn, existing)
        existing[csum].append(fn)
        with open(os.path.join(app.config['FILE_SUMS_LOC']), 'w+', encoding='utf-8') as f:
            json.dump(existing, f)
    return jsonify({'dupeFound': (dupeFile and (dupeFile != fn))}), 200
    
def saveFiles(request, update=False):
    zipped = request.files['file']
    try:
        z = ZipFile(file=zipped, mode='r', compression=zipfile.ZIP_DEFLATED, metadata_encoding='utf-8')
    except:
        return "ERROR: Unable to create ZipFile object"
    
    try:
        for f in z.filelist:
            if not update and pathlib.Path(os.path.join(app.config['UPLOAD_FOLDER']) + f.filename).is_file():
                raise FileExistsError(f"{f.filename} already exists")
            else:
                ZipFile.extract(z, f, os.path.join(app.config['UPLOAD_FOLDER']))
                with open(os.path.join(app.config['UPLOAD_FOLDER']) + f.filename, 'rb') as file:
                    sha256Sum = hashlib.file_digest(file, 'sha256').hexdigest()
                try:
                    with open(os.path.join(app.config['FILE_SUMS_LOC']), 'r', encoding='utf-8') as filesums_r:
                        existing = json.load(filesums_r)
                        remove_fileName_from_checkSums(f.filename, existing)
                        if sha256Sum in existing:
                            existing[sha256Sum].append(f.filename)
                        else:
                            existing[sha256Sum] = [f.filename]
                    with open(os.path.join(app.config['FILE_SUMS_LOC']), 'w+', encoding='utf-8') as filesums_w:
                        json.dump(existing, filesums_w)
                except json.JSONDecodeError as e:
                    with open(os.path.join(app.config['FILE_SUMS_LOC']), 'w+', encoding='utf-8') as filesums_w:
                        json.dump({sha256Sum: [f.filename]}, filesums_w)
    except FileExistsError:
        return f"ERROR: {f.filename} already exists", 409
    except Exception as e:
        print(f"Exception: {e}")
        return "ERROR: Unable to extract files to save"
    return "File(s) Saved"

def getFiles():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    files.remove("fileSums.json")
    return files

def deleteFiles(request):
    json_filenames = json.loads(request.data.decode('utf-8'))
    filenames_str = json_filenames['filenames']
    filenames = str.split(filenames_str, ',')
    for filename in filenames:
        if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'] + filename)):
            with open(os.path.join(app.config['UPLOAD_FOLDER']) + filename, 'rb') as f:
                sha256Sum = hashlib.file_digest(f, 'sha256').hexdigest()
                
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'] + filename))
            
            with open(os.path.join(app.config['FILE_SUMS_LOC']), 'r+', encoding='utf-8') as f:
                existing = json.load(f)
                
            if len(existing[sha256Sum]) > 1:
                existing[sha256Sum].remove(filename)
            else:
                del existing[sha256Sum]
            
            with open(os.path.join(app.config['FILE_SUMS_LOC']), 'w+', encoding='utf-8') as f:
                json.dump(existing, f)
    return True

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

def getWordFreq(limit:int, orderBy:str):
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
    word_list = sorted(word_dict.items(), key=myKey, reverse=(orderBy[0].lower()=='d'))[:limit]
    return word_list

def findDupeFile(sha256Sum, fn):
    try:
        with open(os.path.join(app.config['FILE_SUMS_LOC']), 'r', encoding='utf-8') as f:
            fileSums = json.load(f)
            if sha256Sum in fileSums:
                matchFile = fileSums[sha256Sum]
                if fn in matchFile:
                    return None
                return matchFile[0]
            else:
                return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def remove_fileName_from_checkSums(filename, existing):
    for valuesList in existing.values():
        if filename in valuesList:
            valuesList.remove(filename)
        if len(valuesList) == 0:
            del existing[list(existing.keys())[list(existing.values()).index(valuesList)]]
            break