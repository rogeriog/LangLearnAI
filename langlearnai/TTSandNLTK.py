#import nltk
#from nltk.corpus import words
#english_words = words.words()
#from collections import Counter
#word_counts = Counter(english_words)
#most_common_words = word_counts.most_common(10)
import nltk
import inflect
import wordfreq
from googletrans import Translator
import json, time, re, os
import openai
from gtts import gTTS
from pydub import AudioSegment
from collections import Counter
def single_word(string):
  return len(string.split()) == 1

def get_keywords_in_phrase(phrase):
    # Tokenize the phrase
    tokens = nltk.word_tokenize(phrase)

    # Tag the words with their part of speech
    tagged_tokens = nltk.pos_tag(tokens)

    # Filter the list of words to include only the nouns
    keywords = [word for word, pos in tagged_tokens if pos.startswith('NN') or pos.startswith('VB')]
    filtered_keywords = [s for s in keywords if s not in ['name','names','verbs','words','phrases','related','using','list','following']]
    return filtered_keywords
def get_repeated_elements(lst):
    # Create a counter for the list
    c = Counter(lst)
    repeated_elements = []

    # Iterate over the counter
    for element, count in c.items():
        # If the count is greater than 1, the element is repeated
        if count > 1:
            repeated_elements.append(element)

    return repeated_elements
def remove_element_once(d, element):
    # Iterate over the dictionary
    for key, value in d.items():
        # Check if the element is in the list
        if element in value:
            # Remove the element from the list
            value.remove(element)
            # Break the loop, since we only want to remove the element once
            break
def check_gender_pl_noun(word, languages):
    # Tokenize the word
    wordtk = nltk.word_tokenize(word)
    # to make plural
    p = inflect.engine()
    # Tag the word with part-of-speech tags
    tagged_word = nltk.pos_tag(wordtk)
    article_text=""
    plural_text=""
    # Check if the word is a noun
    if tagged_word[0][1] == "NN":
        word="the "+word
        for lang in languages:
            translated_word = translator.translate(word, dest=lang)
            article_text+=f"({lang}) {translated_word.text}, "
            translated_word = translator.translate(p.plural(word), dest=lang)
            plural_text+=f"({lang}) {translated_word.text}, "
        return article_text+"\n"+plural_text+"\n"
    else:
        return ""
def get_translated_text(translator, list_to_translate, target_languages, generate_audio=True, accum_audio_file=None):
    # Translate the English words into French
    translated_words = []
    for word in list_to_translate:
        print(f"Translating: {word} ")
        translation_text=f"{word}\n"
        for lang in target_languages:
                translated_word = translator.translate(word, dest=lang) 
                try:
                #if ( translated_word.extra_data['all-translations'] is not None) and ('all-translations' in translated_word.extra_data):
                    types_translated=len(translated_word.extra_data['all-translations'])
                    for typ in range(types_translated):
                        typeword=translated_word.extra_data['all-translations'][typ][0]
                        translations=translated_word.extra_data['all-translations'][typ][1]
                        if single_word(word):
                            translation_text+=f"{lang}: {typeword}) {', '.join(translations[:4])}\n"
                        else:
                            translation_text+=f"{lang}: {', '.join(translations[:4])}\n"
                except:
                    try: ## if this particular language doesnt translate go to next
                        translations=translated_word.extra_data['translation'][0][0]
                        try:
                            typeword=translated_word.extra_data['definitions'][0][0]
                        except:
                            try:
                                typeword=translated_word.extra_data['definitions'][0]
                            except: 
                                typeword = 'undefined_type'
                        if single_word(word):
                            translation_text+=f"{lang}: {typeword}) {translations}\n"
                        else:
                            translation_text+=f"{lang}: {translations}\n"
                    except:
                        print(f"COULD NOT TRANSLATE THE WORD: {word} in {lang}")
                        continue

        time.sleep(3) ## so API doesnt complain
        translation_text+=check_gender_pl_noun(word, languages)
        if generate_audio:
            translation_text+=add_short_phrase(word, languages, generate_audio=True, accum_audio_file=accum_audio_file)
        else:
            translation_text+=add_short_phrase(word, languages)
        print(translation_text)
        translated_words.append(translation_text)
    return translated_words
def get_type_word_nltk(word):
    # nltk is surprisingly very bad in filtering single word, openai does a better job
    # Tokenize the word
    wordtk = nltk.word_tokenize(word)
    # to make plural
    p = inflect.engine()
    # Tag the word with part-of-speech tags
    tagged_word = nltk.pos_tag(wordtk)
    return tagged_word[0][1] 

def get_common_words(N):
    exclude_list=['hollywood','virginia','kevin','el','dc','en','tim','jan','jordan','don', 'ohio', 'tony', 'mm', 'll', 'ma', 'et', 'ca', 'ya', 'iii', 'ii', 'joe', 'los', 'van', 'bob', 'michael', 'alex', 'ah']
    most_common_words=[]
    for word in wordfreq.top_n_list('en', N):
        if len(word) > 1 and not word in exclude_list:  
            most_common_words.append(word)
    return most_common_words

def separate_phrase(phrase):
    chunks = re.split(r'[\n,]', phrase)
    chunks = list(filter(lambda x: x != '', chunks))
    return chunks

# def separate_phrase(phrase,n=30):
#     words = phrase.split('')
#     chunks = [words[i:i+n] for i in range(0, len(words), n)]
#     concatenated_chunks = [" ".join(chunk) for chunk in chunks]
#     return concatenated_chunks
def generate_audio_from_lessonsdict(lessons_dict_file, keys=None, target_language='en', accum_audio_file=None, origin_language='en',
                                    sufix='',separate_to_gtts=True, translate_on_spot=False):
    lessons_dict=json.load(open(lessons_dict_file,'r'))
    if keys is not None: ## select subset of keys
        lessons_dict = {key: lessons_dict[key] for key in keys}
    for key in lessons_dict.keys():
        generate_audio_text(lessons_dict[key], target_language, request=None, accum_audio_file=accum_audio_file,
                            orig_lang=origin_language,sufix=sufix,
                            separate_to_gtts=separate_to_gtts,translate_on_spot=translate_on_spot)

def normalize_AudioSegment(audio):
    audio = audio.normalize()
    return audio

def generate_audio_text(text, lang, request=None, accum_audio_file=None,orig_lang='en',sufix='',
                        separate_to_gtts=True, translate_on_spot=False):
    translator = Translator()
    audio_total = AudioSegment.silent(duration=1000, frame_rate=44100)
    if request is not None:
        audio = gTTS(request, lang=orig_lang)
        audio.save("phrase_tmp.mp3")
        audio_phrase = AudioSegment.from_mp3("phrase_tmp.mp3")
        silent_segment = AudioSegment.silent(duration=2000, frame_rate=44100)
        audio_total += audio_phrase + silent_segment
        req_clean = re.sub(r'[^\w\s]', '_', request).replace(' ', '_')+sufix
    if isinstance(text,list):
        text=", ".join(text)
    text = re.sub(r'\(.*?\)', '', text)
    #text = re.sub(r'[^\w\s]', '', text)
    ## reduce phrase in chunks
    if separate_to_gtts:
        phrases=separate_phrase(text)
    else:
        phrases=[text]

    for phrase in phrases: 
        if translate_on_spot:
            phrase = translator.translate(phrase, src=orig_lang, dest=lang).text
        audio = gTTS(phrase, lang=lang)
        time.sleep(2)
        # Save the audio to a file
        audio.save("phrase_tmp.mp3")
        # Load the audio files
        audio_phrase = AudioSegment.from_mp3("phrase_tmp.mp3")
        silent_segment = AudioSegment.silent(duration=1000, frame_rate=44100)
        audio_total += audio_phrase + silent_segment
    silent_segment = AudioSegment.silent(duration=2000, frame_rate=44100)
    audio_total += silent_segment
    time.sleep(3)
    if request is not None:
        try:
            os.mkdir("./audios")
        except:
            pass
        audio_total.export(f"./audios/{req_clean}.mp3", format="mp3")
    if accum_audio_file is not None:
        try :
            audio_accum = AudioSegment.from_mp3(accum_audio_file)
        except : 
            audio_accum = AudioSegment.silent(duration=2000, frame_rate=44100)
            audio_accum.export(accum_audio_file, format="mp3")
        audio_accum += audio_total
        audio_accum = normalize_AudioSegment(audio_accum)
        audio_accum.export(accum_audio_file, format="mp3")
# Download necessary data
# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')
# def generate_dialogue():
"""
try:
    with open('translated_dictionary.json', 'r') as f:
        # Load the JSON data into a Python dictionary
        translated_dict = json.load(f)
except:
    translated_dict = {}
    translated_dict['most_common_words'] = []

try:
    with open('common_words_dictionary.json', 'r') as f:
        # Load the JSON data into a Python dictionary
        commonwords_dict = json.load(f)
except:
    commonwords_dict = {}
    for key in ['verbs','nouns','adjs','advbs','undef']:
        commonwords_dict[key] = []

languages=['fr','de','nl','it']

translator = Translator()
import itertools
allvalues=list(itertools.chain(*list(commonwords_dict.values())))
print(allvalues)
print(commonwords_dict)
for word in most_common_words[:500]:
    if word not in allvalues:
        print(word)
        nltk_word_type=get_type_word(word)
        if nltk_word_type=='VB':
            commonwords_dict['verbs'].append(word)
        elif nltk_word_type=='NN':
            commonwords_dict['nouns'].append(word)
        elif nltk_word_type=='JJ':
            commonwords_dict['adjs'].append(word)
        elif nltk_word_type=='RB':
            commonwords_dict['advbs'].append(word)
        else:
            commonwords_dict['undef'].append(word)
        with open('common_words_dictionary.json', 'w') as f:
            # Write the dictionary to the file in JSON format
            json.dump(commonwords_dict, f)
print(commonwords_dict)
import sys
sys.exit()
translated_dict['most_common_words'].extend(get_translated_text(translator,most_common_words[0:50], languages,
                                                                generate_audio=True,
                                                                accum_audio_file='final_audio.mp3'
                                                                ))
print("-------------------------------------------------------")
print("\n".join(translated_dict['most_common_words']))
with open('translated_dictionary.json', 'w') as f:
    # Write the dictionary to the file in JSON format
    json.dump(translated_dict, f)
print("Saved as translated_dictionary.json")

import sys
sys.exit()

# Open the JSON file
with open('word_dictionary.json', 'r') as f:
    # Load the JSON data into a Python dictionary
    word_dict = json.load(f)

# Create the new dictionary using the keys
for key in word_dict.keys():
    if key not in translated_dict:
        translated_dict[key] = get_translated_text(translator,word_dict[key], languages)
    else:
        translated_dict[key].extend(get_translated_text(translator,word_dict[key], languages))
    time.sleep(5)
    # Open a file for writing
    with open('translated_dictionary.json', 'w') as f:
    # Write the dictionary to the file in JSON format
        json.dump(translated_dict, f)

"""

