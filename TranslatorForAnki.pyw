import PySimpleGUI as sg
import requests # Request to website and download HTML contents
import urllib.request
import json
#import pdb #debugging; pdb.set_trace()


def main():

    ###########################################################
  
    DEEPL_API_KEY = ''
    
    
    ##THE FOLLOWING VARIABLES ARE FOR TEXT TO SPEECH. IF YOU DO NOT WANT/NEED THAT, YOU CAN LEAVE THEM BLANK
    
    ANKI_MEDIA_PATH = 'C:\\Users\\[YOUR USER NAME]\\AppData\\Roaming\\Anki2\\User 1\\collection.media\\' #This is the dafault for newer Anki versions. Your media path may be different.
    IBM_WATSON_TTS_API_KEY = ''
    IBM_WATSON_TTS_URL = ''
    
    
    ############################################################

    
    sg.theme('DarkGrey14')  # Set the theme
    sg.set_options(font=('Arial', 12))
    
    languageList = ['German','Italian','Portuguese','Spanish','Japanese']
    languageCodes = ['de','it','pt','es','ja']
    languageDict = dict(zip(languageList, languageCodes))
    
    lang = "de" #set default language to German
    #Check if AnkiConnect is installed and active
    try:
        if 'AnkiConnect' in requests.get('http://localhost:8765').text:
            actions = [
                {'action':'deckNames'},
                {'action':'modelNames'}
            ]
            ankiData = invoke('multi',actions=actions)
            deckList = ankiData[0]
            modelList = ankiData[1]
            AC_active = 1
    except:
        deckList = ""
        modelList = ""
        AC_active = 0
    
    # Define the layout
    layout = [
        [sg.Text('English                     '), sg.Combo(languageList, default_value="German", readonly=True, enable_events=True, key='-TARGETLANG-')],
        [sg.Multiline(size=(20, 3), key='-ENGLISH-'), sg.Multiline(size=(20, 3), key='-LANG_B-')],
        [sg.Checkbox('Formal', key='-FORMAL-')],
        [sg.Button('Translate'), sg.Button('Clear')],
        [sg.HSep()],
        [sg.Button('Add Note to Anki',button_color='tan2',key='-ANKIADD-'), sg.Checkbox('Flag',key='-ANKIFLAG-')],  
        [sg.Text('Deck:'), sg.Combo(deckList, s=(30,22), enable_events=True, readonly=True, key='-DECK-')],
        [sg.Text('Model:'),sg.Combo(modelList, s=(29,22), enable_events=True, readonly=True, default_value='Basic (and reversed card)',key='-MODEL-')]
    ]

    
    # Create the window
    window = sg.Window('Translator For Anki', layout, element_justification='c', return_keyboard_events=True)

    # Event loop
    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED:
            break
        
        if event == '-TARGETLANG-':
            lang = languageDict[values['-TARGETLANG-']]
        
        if event in ('Translate', 'Enter:28', '\r'):
            if values['-FORMAL-']==True:
                formality = 1
            else:
                formality = 0
                
            # Disable the Translate button and show loading indicator
            window['Translate'].update(disabled=True, button_color=('white', 'gray'))
            window.refresh()
            
            # Run translation
            if window.FindElementWithFocus() == window['-LANG_B-']:
                sourceText = values['-LANG_B-']
                getTranslation(sourceText, lang, formality, 0, window, DEEPL_API_KEY)
            else:
                sourceText = values['-ENGLISH-']
                getTranslation(sourceText, lang, formality, 1, window, DEEPL_API_KEY)
        
        
        if event in ('Clear','Escape:27'):
            window['-LANG_B-'].update("")
            window['-ENGLISH-'].update("")
    
    
        ##ANKI Stuff
        if event == '-ANKIADD-' and AC_active == 1:
            try:
                audio = " [sound:" + TTS(values['-LANG_B-'],lang, IBM_WATSON_TTS_API_KEY, IBM_WATSON_TTS_URL, ANKI_MEDIA_PATH) + "]"
            except:
                audio = ""
            fields = {
                'Front': values['-LANG_B-'] + audio,
                'Back': values['-ENGLISH-']
            }
            if values['-ANKIFLAG-'] == 1:
                tags = ["marked","added"]
            else:
                tags = ["added"]
            addNote(values['-DECK-'],values['-MODEL-'],fields,tags)
            
    
    # Close the window
    window.close()

    return


def getTranslation(source, lang, formal, direction, window, api_key):

    sourceFormatted = source.replace(" ","+")

    if formal == 0:
        formalityString = "less"
    else:
        formalityString = "more"
        
        
    if direction == 1:
        sourceLang = "EN"
        targetLang = lang
        data = 'text='+sourceFormatted + '&target_lang='+targetLang+'&source_lang='+sourceLang+'&formality=' + formalityString
    else:
        sourceLang = lang
        targetLang = "EN"
        data = 'text='+sourceFormatted + '&target_lang='+targetLang+'&source_lang='+sourceLang
    

    headers = {
        'Authorization': 'DeepL-Auth-Key ' + api_key,
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    res = requests.post('https://api-free.deepl.com/v2/translate', headers=headers, data=data)
    translation = json.loads(res.text)["translations"][0]["text"]
    
    if direction == 1:
        # Update the German text box with the translation
        window['-LANG_B-'].update(translation)
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


def TTS(text, lang, api_key, url, media_path):
    headers = {
        'Content-Type': 'application/json',
    }

    json_data = {
        'text': text,
    }
    voiceDict = {'de':'de-DE_BirgitV3Voice','it':'it-IT_FrancescaV3Voice','pt':'pt-BR_IsabelaV3Voice','es':'es-LA_SofiaV3Voice','ja':'ja-JP_EmiV3Voice'}
    
    try:
        voiceName = voiceDict[lang]
        
        response = requests.post(
            url + '/v1/synthesize?voice=' + voiceName + '&rate_percentage=-10',
            headers=headers,
            json=json_data,
            auth=('apikey', api_key),
        )
        
        filename = "".join(x for x in text if x.isalnum())
        path = media_path + filename + ".ogg"
        with open(path, "wb") as f:
            f.write(response.content)
        
        filenamefull = filename + ".ogg"
        return filenamefull
        
    except Exception as e:
        print(e)
        return

main()