import os, re, time
import json
import genanki
import googletrans
import LangDeckGen
import zipfile, os
import shutil
import sqlite3
def separate_words(phrase):
    chunks = re.split(r'[\n, ]', phrase)
    chunks = [re.sub(r'[^\w\s\'\-]','',x) for x in  chunks]
    chunks = list(filter(lambda x: x != '', chunks))
    chunks = list(set([x.replace('\n','').lower().strip() for x in chunks]))
    return chunks

def get_words_from_JSON_files(directory='.',jsonfiles=None,writeto=None):
    # create an empty list to store the words
    words = []
    # loop through all the files in the directory
    if jsonfiles is None:
        jsonfiles=os.listdir(directory)
    else:
        if isinstance(jsonfiles,str):
            jsonfiles=[jsonfiles]
    for filename in jsonfiles:
        # only process json files
        if filename.endswith('.json'):
            # open the json file and load the data
            filepath = os.path.join(directory, filename)
            with open(filepath) as json_file:
                data = json.load(json_file)
                # loop through all the keys in the json data
                for key in data:
                    # check if the key contains a list of words
                    if isinstance(data[key], list):
                        # add the words to the list
                        pass # words += data[key]
                    else:
                        words_to_add = separate_words(data[key])
                        words += words_to_add
    final_word_list=sorted(list(set(words)))
    ## write to file
    if writeto is not None:
        text="\n".join(final_word_list)
        with open(writeto, "w") as f:
            f.write(text)
    return final_word_list

def get_entries_from_apkg(apkg_file):
    try:
        os.mkdir("apkgtmp")
    except:
        pass
    with zipfile.ZipFile(apkg_file, 'r') as zip_ref:
        zip_ref.extractall("./apkgtmp")
    conn = sqlite3.connect('./apkgtmp/collection.anki2')
    cursor = conn.cursor()
    cursor.execute('SELECT flds FROM notes')
    result = cursor.fetchall()
    cards_apkg=[]
    for i in range(len(result)):
        cards_apkg.append(result[i][0].split('\x1f')[0])
    shutil.rmtree("./apkgtmp")
    return cards_apkg
