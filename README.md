# Anki Translator

This repo serves as a tool to streamline the creation of langauge-learning flashcards in Anki. The program allows translation between English and a target langauge and the creation of Anki flashcards with text-to-speech audio. Usage of this script requires personal attainment of [DeepL](https://www.deepl.com/pro-api?cta=header-pro-api) and [Azure](https://azure.microsoft.com/en-us/free/ai-services/#all-free-services) API keys for translation and text-to-speech services, respectively.


## Setup
1. Make sure you have the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) addon installed in Anki. This allows external programs to add/edit/remove cards in Anki.

2. Attain API keys for DeepL and Azure TTS. Follow [this link](https://www.deepl.com/pro-api?cta=header-pro-api) to create a DeepL account and attain a key. The process for an Azure API key is a bit more convoluted. Follow [this link)[https://azure.microsoft.com/en-us/free/ai-services/#all-free-services] and create a **free** account. As of writing this, a free account with Azure will get you 500,000 characters per month.

3. Open the Setup.json file and paste your API keys in their respective field. Also, input the path for your Anki "collection.media" folder.

4. Next, run the following to install python dependencies.
```
pip install -r requirements.txt
```

5. Finally, you can run the following to start the GUI. I like to use AutoHotKey to bind the program to a keyboard shortcut for easy access.
```
python TranslatorForAnki.pyw
```

## Use
**Anki must be running for the script to function!**

The program will detect which langauge to translate to/from based on the text box the cursor is active in. If the course is active in the "English" text box, it will transalte to the target language, and vise versa.