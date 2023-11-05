import PySimpleGUI as sg
import requests # Request to website and download HTML contents
import urllib.request
import json
import threading
import pyperclip
import azure.cognitiveservices.speech as speechsdk
# import pdb #debugging; pdb.set_trace()


def main():
    sg.theme('DarkGrey14')  # Set the theme
    sg.set_options(font=('Arial', 12))
    
    
    # decks = invoke('deckNames')
    # treedata = sg.TreeData()
    # for deck in decks:
        # parts = deck.split('::')
        # if len(parts)==1:
            # parent = ""
            # name = parts[0]
        # else:
            # parent = parts[len(parts)-2]
            # name = parts[len(parts)-1]
        # treedata.Insert(parent,name,name,deck)
    
    
    try:
        if 'AnkiConnect' in requests.get('http://localhost:8765').text:
            comboList = invoke('deckNames')
            AC_active = 1
    except:
        comboList = ""
        AC_active = 0
    
    # Define the layout
    layout = [
        [sg.Text('English                  '), sg.Text('                 German')],
        [sg.Multiline(size=(20, 3), key='-ENGLISH-'), sg.Multiline(size=(20, 3), key='-GERMAN-')],
        [sg.Checkbox('Formal', key='-FORMAL-')],
        [sg.Button('Translate'), sg.Button('Clear')],
        [sg.HSep()],
        [sg.Button('Audio',key= '-GETAUDIO-'),sg.Button('Add Note to Anki',button_color='tan2',key='-ANKIADD-'), sg.Checkbox('Flag',key='-ANKIFLAG-')],  
        [sg.Text('Deck:'), sg.Combo(comboList, default_value = 'German::German A1::Misc. Phrases', s=(30,22), enable_events=True, readonly=True, key='-COMBO-')]
    ]

    
    # Create the window
    window = sg.Window('Translator Thing', layout, element_justification='c', return_keyboard_events=True)

    # Event loop
    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED:
            break

        if event in ('Translate', 'Enter:28', '\r'):
            if values['-FORMAL-']==True:
                formality = 1
            else:
                formality = 0
                
            # Disable the Translate button and show loading indicator
            window['Translate'].update(disabled=True, button_color=('white', 'gray'))
            window.refresh()
            
            # Run translation in a separate thread
            if window.FindElementWithFocus() == window['-GERMAN-']:
                sourceText = values['-GERMAN-']
                thread = threading.Thread(target=getTranslation, args=(sourceText, formality, 0, window))
            else:
                sourceText = values['-ENGLISH-']
                thread = threading.Thread(target=getTranslation, args=(sourceText, formality, 1, window))
            
            thread.start()           
        
        if event in ('Clear','Escape:27'):
            window['-GERMAN-'].update("")
            window['-ENGLISH-'].update("")
    
    
        ##ANKI shit
        if event == '-ANKIADD-' and AC_active == 1:
            fields = {
                'Front': values['-GERMAN-'] + " [sound:" + TTS(values['-GERMAN-']) + "]",
                'Back': values['-ENGLISH-']
            }
            if values['-ANKIFLAG-'] == 1:
                tags = ["marked","added"]
            else:
                tags = ["added"]
            addNote(values['-COMBO-'],'Basic (and reversed card, with example)',fields,tags)
        
        if event == '-GETAUDIO-':
            pyperclip.copy(TTS(values['-GERMAN-']))
    
    # Close the window
    window.close()

    return


def getTranslation(source, formal, en2de, window):

    sourceFormatted = source.replace(" ","+")

    if formal == 0:
        formalityString = "less"
    else:
        formalityString = "more"
        
        
    if en2de == 1:
        sourceLang = "EN"
        targetLang = "DE"
        data = 'text='+sourceFormatted + '&target_lang='+targetLang+'&source_lang='+sourceLang+'&formality=' + formalityString
    else:
        sourceLang = "DE"
        targetLang = "EN"
        data = 'text='+sourceFormatted + '&target_lang='+targetLang+'&source_lang='+sourceLang
    

    headers = {
        'Authorization': 'DeepL-Auth-Key 76e05505-7b45-e57b-5e49-8d51dfa76b59:fx',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    res = requests.post('https://api-free.deepl.com/v2/translate', headers=headers, data=data)
    translation = json.loads(res.text)["translations"][0]["text"]
    
    if en2de == 1:
        # Update the German text box with the translation
        window['-GERMAN-'].update(translation)
    else:
        # Update the English text box with the translation
        window['-ENGLISH-'].update(translation)
    
    # Enable the Translate button and hide loading indicator
    window['Translate'].update(disabled=False, button_color=('black', 'white'))
    window.refresh()
    
    return
    
    
def addNote(deck_name, model_name, fields, tags=None):
    # API endpoint for AnkiConnect
    url = 'http://localhost:8765'

    # Prepare the request payload
    payload = {
        'action': 'addNote',
        'version': 6,
        'params': {
            'note': {
                'deckName': deck_name,
                'modelName': model_name,
                'fields': fields,
                'tags': tags,
            }
        }
    }

    try:
        # Make the POST request to AnkiConnect
        response = requests.post(url, data=json.dumps(payload))

        # Check the response status
        if response.status_code == 200:
            result = json.loads(response.text)
            if 'error' in result:
                print('AnkiConnect Error:', result['error'])
            else:
                print('Note added successfully:', result['result'])
        else:
            print('AnkiConnect request failed. Status Code:', response.status_code)

    except requests.exceptions.RequestException as e:
        print('AnkiConnect request failed:', str(e))
    
    return

def request(action, **params):
    return {'action': action, 'params': params, 'version': 6}

def invoke(action, **params):
    requestJson = json.dumps(request(action, **params)).encode('utf-8')
    response = json.load(urllib.request.urlopen(urllib.request.Request('http://localhost:8765', requestJson)))
    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']


def TTS(text):
    # Creates an instance of a speech config with specified subscription key and service region.
    speech_key = "0351fa90f15444568a5b09cede020130"
    service_region = "centralus"

    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.SpeechSynthesisLanguage = "de-AT"
    speech_config.speech_synthesis_voice_name = "de-AT-JonasNeural"
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio48Khz96KBitRateMonoMp3)
    
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    
    ssml_text = """
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="de-AT">
        <voice name="de-AT-JonasNeural">
            <prosody rate=".85">
                {text}
            </prosody>
        </voice>
    </speak>
    """.format(text=text)
    
    filename = "".join(x for x in text if x.isalnum())
    path = "C:\\Users\\dylan\\AppData\\Roaming\\Anki2\\User 1\\collection.media\\" + filename + ".mp3"
    
    filenamefull = filename + ".mp3"
    
    result = speech_synthesizer.speak_ssml_async(ssml_text).get()
    stream = speechsdk.AudioDataStream(result)
    stream.save_to_wav_file(path)
    
    return filenamefull

main()