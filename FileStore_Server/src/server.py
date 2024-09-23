import hashlib
import os
from flask import Flask, jsonify, request
import pathlib
import zipfile
from zipfile import ZipFile
import json
import shutil

UPLOAD_FOLDER = str(pathlib.Path(__file__).parent.parent.resolve().joinpath("resources").joinpath("filestore"))
FILE_SUMS_LOC = str(pathlib.Path(UPLOAD_FOLDER).joinpath("fileSums.json"))

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['FILE_SUMS_LOC'] = FILE_SUMS_LOC

####################################
#
#  API Endpoints
#
####################################
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

@app.route("/copydupe", methods=["POST"])
def copyDupeIfExists():
    csum =  request.args.get('sha256', type=str)
    fn = request.args.get('fileName', type=str)
    dupeFile = findDupeFile(csum, fn) or False
    if dupeFile and dupeFile != fn:
        shutil.copyfile(os.path.join(app.config['UPLOAD_FOLDER'], dupeFile), os.path.join(app.config['UPLOAD_FOLDER'], fn))
        with open(os.path.join(app.config['FILE_SUMS_LOC']), 'r+', encoding='utf-8') as f:
            existing = json.load(f)
        removeFileNameFromCheckSums(fn, existing)
        existing[csum].append(fn)
        with open(os.path.join(app.config['FILE_SUMS_LOC']), 'w+', encoding='utf-8') as f:
            json.dump(existing, f)
    return jsonify({'dupeFound': (dupeFile and (dupeFile != fn))}), 200
    
########################################################
#
# Util Functions
#
########################################################
def saveFiles(request, update=False):
    """
    saveFiles() opens the uploaded zip archive and executes the file saves or updates for all files
    in the archive.

    :param request: the full HTTP request object
    :param update: boolean flag indicating if we are allowed to update existing files or else return Error if the file exists
    :return: returns result message as string and status code
    """
    zipped = request.files['file']
    try:
        z = ZipFile(file=zipped, mode='r', compression=zipfile.ZIP_DEFLATED, metadata_encoding='utf-8')
    except:
        return "ERROR: Unable to create ZipFile object", 500
    
    try:
        for f in z.filelist:
            # if we are executing an 'add' command and the file exists then raise an error and return 409 status code
            if not update and pathlib.Path(os.path.join(app.config['UPLOAD_FOLDER'], f.filename)).is_file():
                raise FileExistsError(f"{f.filename} already exists")
            else:
                ZipFile.extract(z, f, os.path.join(app.config['UPLOAD_FOLDER']))
                with open(os.path.join(app.config['UPLOAD_FOLDER'], f.filename), 'rb') as file:
                    sha256Sum = hashlib.file_digest(file, 'sha256').hexdigest()
                try:
                    with open(os.path.join(app.config['FILE_SUMS_LOC']), 'r', encoding='utf-8') as filesums_r:
                        # get existing records from fileSums.json
                        existing = json.load(filesums_r)

                        # remove an existing record for f.filename if one exists
                        # this is to account for updated files having a new sha256 value and we want to remove the previous record
                        removeFileNameFromCheckSums(f.filename, existing)

                        # add record for f.filename with its current sha256 checksum
                        if sha256Sum in existing:
                            existing[sha256Sum].append(f.filename)
                        else:
                            existing[sha256Sum] = [f.filename]

                    # rewrite fileSums.json with updated records
                    with open(os.path.join(app.config['FILE_SUMS_LOC']), 'w+', encoding='utf-8') as filesums_w:
                        json.dump(existing, filesums_w)
                except json.JSONDecodeError as e:
                    # this exception occurs when fileSums.json does not exist and the json.load() execution fails
                    # create the file and its first record
                    with open(os.path.join(app.config['FILE_SUMS_LOC']), 'w+', encoding='utf-8') as filesums_w:
                        json.dump({sha256Sum: [f.filename]}, filesums_w)
    except FileExistsError:
        return f"ERROR: {f.filename} already exists", 409
    except Exception as e:
        print(f"Exception: {e}")
        return "ERROR: Unable to extract files to save", 500
    return "File(s) Saved", 200

def getFiles():
    """
    getFiles() returns a list of all files in the filestore directory sorted
    in alphabetical order

    :return: iist of current contents of the filestore
    """
    try:
        # get all files from the resources/filestore directory
        files = os.listdir(app.config['UPLOAD_FOLDER'])

        # remove our internal json file from the return object
        if "fileSums.json" in files:
            files.remove("fileSums.json")

        return sorted(files)
    except FileNotFoundError:
        return "No files found"
    except Exception as e:
        print(f"ERROR: {e}")
        return "Error retrieving files"

def deleteFiles(request):
    """
    deleteFiles() removes a selection of files from the filestore

    :param request: the HTTP request object
    :return: boolean indicating success
    """
    try:
        json_filenames = json.loads(request.data.decode('utf-8'))
        filenames_str = json_filenames['filenames']
        filenames = str.split(filenames_str, ',')
        for filename in filenames:
            # if 'filename' exists in filestore then calculate sha256 to help with removing
            # entry in fileSums.json
            if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb') as f:
                    sha256Sum = hashlib.file_digest(f, 'sha256').hexdigest()

                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                # load existing files from fileSums.json
                with open(os.path.join(app.config['FILE_SUMS_LOC']), 'r+', encoding='utf-8') as f:
                    existing = json.load(f)

                # if the values list for the sha256 key has multiple files then we only remove
                # the filename from the list. if the values list only has one file then we remove
                # the sha256 key and its values list from the 'existing' dictionary
                if len(existing[sha256Sum]) > 1:
                    existing[sha256Sum].remove(filename)
                else:
                    del existing[sha256Sum]

                # write the updated 'existing' dictionary out to fileSums.json
                with open(os.path.join(app.config['FILE_SUMS_LOC']), 'w+', encoding='utf-8') as f:
                    json.dump(existing, f)
        return True
    except:
        return False

def getAllWordsInFile(file):
    """
    getAllWordsInFile() opens a file and populates a list of all words within the file

    :param file: file to get words from
    :return: list of strings. each string is a word from the file
    """
    with open(app.config['UPLOAD_FOLDER'] + file, "r") as f:
        # create a list of each word in the file by iterating over each word in a line while
        # also iterating over each line in the file and using the split() operator
        words = [word for line in f for word in line.rstrip().split()]

    return words

def getWordCount():
    """
    getWordCount() iterates through all files in the filestore and returns the word count for each file

    :return: list of strings. each string specifying the filename and its word count
    """
    files = getFiles()
    result = ""

    # if no files exist in filestore then return now
    if (len(files) == 0):
        return "No files currently stored"
    
    for file in files:
        words = getAllWordsInFile(file)
        result += f"{file} wordcount = {len(words)}\n"
    return result[:-1]

# helper function for the getWordFreq() function. used as a custom key function for the sorted() call
def myKey(t):
    return t[1],t[0]

def getWordFreq(limit:int, orderBy:str):
    """
    getWordFreq() iterates through all files in the filestore and the frequency of each word that exists
    within all files of the filestore

    :param limit: limit the return to this number of words
    :param orderBy: sort the return list in this order
    :return: list of words and their corresponding frequencies
    """
    files = getFiles()
    word_dict = {}

    # if no files exist in filestore then return now
    if (len(files) == 0):
        return "No files currently stored"
    
    for file in files:
        # get list of words in the file
        words = getAllWordsInFile(file)
        
        # for each word we check the dictionary and increment the frequency value if it exists or else
        # insert the word with the initial frequency value of 1
        for word in words:
            # strip any periods or commas off of the end of words
            if word[-1] == '.' or word[-1] == ',':
                word = word[:-1]

            # convert the word to lower case before inserting into or searching the dictionary to prevent
            # 'this' being treated as a different word from 'This'
            word = word.lower()
            word_dict.update({word: (word_dict.get(word) + 1) if word_dict.get(word) else 1})
            
    # create a list from the dictionary and sort based on the orderBy param
    word_list = sorted(word_dict.items(), key=myKey, reverse=(orderBy[0].lower()=='d'))[:limit]
    word_list = jsonify(word_list)
    return word_list

def findDupeFile(sha256Sum, fileName):
    """
    findDupeFile() checks if the filestore contains any files with matching sha256 values
    to the one passed in

    :param sha256Sum: checksum value of the file to find dupe of
    :param fileName: name of the file to find dupe of. used to ensure we don't return itself
    :return: name of dupe file if exists, else None
    """
    try:
        with open(os.path.join(app.config['FILE_SUMS_LOC']), 'r', encoding='utf-8') as f:
            # get existing records from fileSums.json
            existing = json.load(f)

            # check if the requested sha256 checksum appears in the existing fileSums.json
            if sha256Sum in existing:
                matchFile = existing[sha256Sum]

                # if the requested fileName was found in fileSums.json then we return None to 
                # indicate no dupe because the file itself already exists
                if fileName in matchFile:
                    return None
                
                # we found a dupe and it's not the requested file itself. This match is a List
                # of filenames which match the sha256 so we just return the first value of the List
                return matchFile[0]
            else:
                # no match found for the sha256 value
                return None
    except FileNotFoundError as fnfe:
        # this would happen if the filestore was not initialize and the fileSums.json file was not found
        # lets initialize the filestore
        filestore = pathlib.Path(app.config['UPLOAD_FOLDER'])
        filestore.mkdir(parents=True, exist_ok=True)

        # create the fileSums.json file
        with open(os.path.join(app.config['FILE_SUMS_LOC']), 'w+', encoding='utf-8') as f:
            print(f"Initialized Filestore")

        return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def removeFileNameFromCheckSums(filename, existing):
    """
    removeFileNameFromCheckSums() removes the specified filename from the existing fileSums.json archive

    :param filename: name of the file to remove from fileSums.json
    :param existing: the existing fileSums.json archive
    """
    for valuesList in existing.values():
        if filename in valuesList:
            valuesList.remove(filename)
        if len(valuesList) == 0:
            del existing[list(existing.keys())[list(existing.values()).index(valuesList)]]
            break