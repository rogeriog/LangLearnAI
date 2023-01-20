import re,os,time
import openai
import nltk
import json
from collections import Counter
from TTSandNLTK import get_keywords_in_phrase, generate_audio_text
# Download necessary data
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

import pycountry
def get_lang_abbreaviation(language_name):
    try:
        language = pycountry.languages.get(name=language_name)
        return language.alpha_2
    except:
        return None
def edit_dictionary(dictionary_file, keys_to_edit, lambdafunction):
    for key in keys_to_edit:
        if key in d:
            d[key] = lambda_function(d[key])
    return d
    

def get_type_word_openAI(word):
    response = openai.Completion.create(
      model="text-davinci-003",
      prompt=f"most common nltk postag of the word '{word}'? don't describe, only give the postag.",
      temperature=0.3,
      max_tokens=100,
      top_p=1.0,
      frequency_penalty=0.0,
      presence_penalty=0.0
    )
    time.sleep(5)
    nltk_guess=response['choices'][0]['text'].strip()
    nltk_guess=re.sub(r'[^\w\s]', '', nltk_guess)
    nltk_guess=nltk_guess.split()
    penn_treebank_pos = ["CC", "CD", "DT", "EX", "FW", "IN", "JJ", "JJR", "JJS", "LS", "MD", "NN", "NNS", "NNP", "NNPS", "PDT", "PRP", "PRP$", "RB", "RBR", "RBS", "RP", "SYM", "TO", "UH", "VB", "VBD", "VBG", "VBN", "VBP", "VBZ", "WDT", "WP", "WP$", "WRB"]
    for guess in nltk_guess:
        if guess in penn_treebank_pos:
            return guess


def generate_language_lesson_topics(language='english',sleep_interval=5,lesson_topics_file='lesson_topics.json',
                                    custom_request=None):
    try:
        lesson_topics=json.load(open(lesson_topics_file,"r"))
    except:
        lesson_topics={}
    requests=[('vocab',f'give me 80 topics for beginner vocabulary in foreign language, different areas of life. Just give a comma separated list as response, not numbered. Do not repeat.'),
              ('grammar',f'give me 30 topics common to any foreign language grammar textbook, give it as a comma separated list in order of complexity. Do not number, do not repeat topics.')
              ]
    ### if custom request for lesson topics is given
    if custom_request is not None:
        requests.append(custom_request)
    ## make request
    for type_lesson, request in requests:
        if type_lesson in lesson_topics.keys():
            print("This lesson is already available in the written dictionary.") 
            print("You can give a custom request in the format 'custom_request=('dict_key', 'open ai request')")
            continue
        response = openai.Completion.create(
          model="text-davinci-003",
          prompt=f"{request}.",
          temperature=0.3,
          max_tokens=3950,
          top_p=1.0,
          frequency_penalty=0.0,
          presence_penalty=0.0
        )
        time.sleep(sleep_interval) # Sleep for 3 seconds
        print("Done")
        fullresponse=response['choices'][0]['text']
        lesson_topics[type_lesson]=fullresponse.split(',')
    return lesson_topics

def generate_language_lesson(lesson_requests, target_language='english', 
                             generate_audio=True, accum_audio_file='lesson_audios.mp3',origin_language='english',
                             sleep_interval=5,lessons_dictionary='lessons.json',mode='generic'):
    lang_token=get_lang_abbreaviation(target_language)
    orig_lang=get_lang_abbreaviation(origin_language)
    #print(lang_token,orig_lang)
    try:
        lesson_dict=json.load(open(lessons_dictionary, 'r'))
    except:
        lesson_dict = {}
    for request in lesson_requests:
        ## skip lessons already generated
        if f"{request}_{lang_token}_{mode}" in lesson_dict.keys():
            continue
        if mode == 'generic':
            lesson_request=f'make a {target_language} language lesson about "{request}".'
        elif mode == 'vocab':
            lesson_request=f'give me {target_language} vocabulary related to "{request}". Show {origin_language} translations between parenthesis.'
        elif mode == 'grammar':
            lesson_request=f'make a {target_language} grammar lesson about "{request}".'
        elif mode == 'dialog':
            lesson_request=f'make a {target_language} dialog using vocabulary related to "{request}". Dont show person 1, person 2, just the phrases. Do not translate and it must be as long as about 200 words.'
        elif mode == 'dialog_from_words':
            lesson_request=f'make a {target_language} dialog try use the following words "{request}". Dont show person 1, person 2, just the phrases. Do not translate and it must be as long as about 300 words.'
        response = openai.Completion.create(
          model="text-davinci-003",
          prompt=f"{lesson_request}.",
          temperature=0.3,
          max_tokens=3950,
          top_p=1.0,
          frequency_penalty=0.0,
          presence_penalty=0.0
        )
        time.sleep(sleep_interval) # Sleep for 3 seconds
        print("Done")
        fullresponse=response['choices'][0]['text']
        lesson_dict[f"{request}_{lang_token}_{mode}"]=fullresponse
        # Open a file for writing
        with open(lessons_dictionary, 'w') as f:
            # Write the dictionary to the file in JSON format
            json.dump(lesson_dict, f)
        if generate_audio:
            generate_audio_text(fullresponse, lang_token, request=request, accum_audio_file=accum_audio_file,
                                orig_lang=orig_lang, sufix=mode)

def add_short_phrase(word, languages,generate_audio=True, accum_audio_file=None,orig_lang='en'):
    phrase_text=""
    response = openai.Completion.create(
      model="text-davinci-003",
      prompt=f"give me one short phrase containing '{word}', dont describe",
      temperature=0.3,
      max_tokens=100,
      top_p=1.0,
      frequency_penalty=0.0,
      presence_penalty=0.0
    )
    time.sleep(3)

    phrase=response['choices'][0]['text'].strip()
    phrase_text+=phrase+'\n'
    translator = Translator()
    audio_total = AudioSegment.silent(duration=1000, frame_rate=44100)
    orig_phrase=True
    for lang in languages:
        translated_phrase = translator.translate(phrase, dest=lang).text
        phrase_text+=f"{lang}) {translated_phrase}\n"
        if generate_audio:
            if orig_phrase:
                audio = gTTS(phrase, lang=orig_lang)
                audio.save("phrase_tmp.mp3")
                audio_phrase = AudioSegment.from_mp3("phrase_tmp.mp3")
                silent_segment = AudioSegment.silent(duration=2000, frame_rate=44100)
                audio_total += audio_phrase + silent_segment
                orig_phrase=False
            audio = gTTS(translated_phrase, lang=lang)
            time.sleep(1)
            # Save the audio to a file
            audio.save("phrase_tmp.mp3")
            # Load the audio files
            audio_phrase = AudioSegment.from_mp3("phrase_tmp.mp3")
            silent_segment = AudioSegment.silent(duration=2000, frame_rate=44100)
            audio_total += audio_phrase + silent_segment
    time.sleep(3)
    if generate_audio:
        if accum_audio_file is not None:
            try :
                audio_accum = AudioSegment.from_mp3(accum_audio_file)
            except : 
                audio_accum = AudioSegment.silent(duration=2000, frame_rate=44100)
                audio_accum.export(accum_audio_file, format="mp3")
            audio_accum += audio_total
            audio_accum.export(accum_audio_file, format="mp3")
        phrase_clean = re.sub(r'[^\w\s]', '_', phrase).replace(' ', '_')
        try:
            os.mkdir("./audio_phrases")
        except:
            pass
        audio_total.export(f"./audio_phrases/phrase_{phrase_clean}.mp3", format="mp3")
    return phrase_text

def generate_grouped_dictionary(requests,dict_name='grouped_word_dict.json'):
    word_dict= {}
    allwords= []
    try:
        # Open the file for reading
        with open(dict_name, 'r') as f:
            # Load the dictionary from the file
            word_dict = json.load(f)
        allwords = [word for sublist in word_dict.values() for word in sublist]
    except:
        pass

    for request, number in requests:
        ## get keywords in phrase to classify the vocabulary
        keyword=" ".join(get_keywords_in_phrase(request))
        print(request)
        response = openai.Completion.create(
          model="text-davinci-003",
          prompt=f"Give me {number} {request}.",
          temperature=0.3,
          max_tokens=100,
          top_p=1.0,
          frequency_penalty=0.0,
          presence_penalty=0.0
        )
        time.sleep(5) # Sleep for 3 seconds
        print("Done")
        fullresponse=response['choices'][0]['text']
        listwords=re.sub(r"\n[0-9]+\.",",",response['choices'][0]['text']).split(',')
        listwords=[word.strip() for word in listwords]
        for value in listwords:
            if value == '':
                listwords.remove('')
            elif len(value) == 1:
                listwords.remove(value)
        if keyword in word_dict:
            word_dict[keyword].extend(listwords)
        else:
            word_dict[keyword] = listwords
        # Open a file for writing
        with open('word_dictionary_tmp.json', 'w') as f:
            # Write the dictionary to the file in JSON format
            json.dump(word_dict, f)

    allwords = [word for sublist in word_dict.values() for word in sublist]
    repeated = get_repeated_elements(allwords)
    for element in repeated:
        remove_element_once(word_dict, element)
    print(f"Following elements repeated: {repeated}")

    word_dict["others"]=word_dict[""]
    del word_dict[""]

    # Open a file for writing
    with open(dict_name, 'w') as f:
        # Write the dictionary to the file in JSON format
        json.dump(word_dict, f)
    # remove remaining tmp file
    os.remove('word_dictionary_tmp.json')
