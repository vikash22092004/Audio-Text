from flask import Flask, send_file, render_template, request, redirect
from PyPDF2 import PdfReader
from englisttohindi.englisttohindi import EngtoHindi
from gtts import gTTS
import os
import speech_recognition as sr
from translate import Translator
import webbrowser


app = Flask(__name__)

globalvarquery = None
globalvartt = None

@app.route('/')
def index():
    return render_template('index.html')

#PDF Translator 
def pdf_extract(pdf_path, check,num):
    x = pdf_path.split('\\')
    mp3filenm = x[-1] + ".mp3"
    txtfilenm = x[-1] + ".txt"
    reader = PdfReader(pdf_path)
    length = len(reader.pages)
    translated_text = ""

    with open(txtfilenm, 'w', encoding='utf-8') as output_file:
        print(f"There are {length} Pages")
        
        loop = True
        try:
            while loop:
                if check:
                    for i in range(length):
                        lines = pdf_reader(pdf_path, i)
                        print(f"Page Number {i}:\n")
                        output_file.write(f"\nPage Number {i}:\n")
                        for line in lines:
                            translated_line = translate_to_hindi(line)
                            if translated_line is not None:
                                print(translated_line + "\n")
                                output_file.write(translated_line + "\n")
                                translated_text += translated_line + "\n"
                    break
                else:
                    Page=int(num)-1
                    lines = pdf_reader(pdf_path, Page)
                    for line in lines:
                        translated_line = translate_to_hindi(line)
                        if translated_line is not None:
                            print(translated_line)
                            output_file.write(translated_line + "\n")
                            translated_text += translated_line + "\n"
                    loop = False
                save_audio_to_mp3(translated_text, to_lang='hi', file_name=mp3filenm)
        except:
            return redirect('/error')
    return translated_text
def pdf_reader(reader, page):
    extract = PdfReader(reader)
    Page = extract.pages[page]
    text = Page.extract_text()
    lines = text.split('\n')

    return lines
def translate_to_hindi(text):
    translator = EngtoHindi(text)
    return translator.convert



@app.route('/download_pdf', methods=['GET', 'POST'])
def download_pdf():
    if request.method == 'POST':
        document_path = request.form['pdfname'] + ".pdf.txt"
    try:
        return send_file(document_path, as_attachment=True)
    except:
        return render_template('download_pdf.html')
@app.route('/download_audpdf', methods=['GET', 'POST'])
def download_audpdf():
    
    if request.method == 'POST':
        document_path = request.form['pdfname'] + ".pdf.mp3"
    try:
        return send_file(document_path, as_attachment=True)
    except:
        return render_template('download_audpdf.html')       
@app.route('/pdf_translator', methods=['GET', 'POST'])
def pdf_translator():
    tt="Nothing Translated Yet"
    try:
        if request.method == 'POST':
            reader = request.form['pdf_file']
            choice = request.form['translation_type'].strip().upper()
            num = request.form['num']
            check = True if choice == 'A' else False

            tt=pdf_extract(reader, check,num)
    except:
        return redirect('/error')
    return render_template('pdf_translator.html',pdftxt=tt)


#Speech To Speech Translation
def take_command(timeout=10):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=timeout)
            print("Recognizing...")
            query = recognizer.recognize_google(audio, language='en-in')
            print(f"You said: {query}")
            print(type(query))
            return query
        except sr.WaitTimeoutError:
            print("Speech recognition timed out. No speech detected.")
            return None
        except sr.UnknownValueError:
            print("Speech recognition could not understand audio.")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return None


def save_translation_to_txt(translated_text, file_name = "STS-TranslatedTextFile.txt"):
    try:
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(translated_text)
    except:
        return redirect('/error')
        
@app.route('/speech_translator')
def speech_translator():
    return render_template('speech_translator.html')
@app.route('/speech_translator1', methods=['GET','POST'])
def speech_translator1():
    global globalvarquery
    global globalvartt
    try:
        if request.method == 'POST':

        
            translate = True
            x = None
            query=None
            translated_text=None
            while translate:
                print("Say the sentence you want to translate once you see the word 'Listening'")
                while query is None:
                    query = take_command()

                to_lang = request.form['lang'].lower()
                translator = Translator(to_lang=to_lang)
                globalvarquery=query
                try:
                    translated_text = translator.translate(query)
                    globalvartt=translated_text
                    print(f"Translated text ({to_lang}): {translated_text}")
                    save_translation_to_txt(translated_text)
                    print("Translated text saved to 'translated_text.txt'")

                    save_audio_to_mp3(translated_text, to_lang)
                    print("Translated audio saved to 'translated_audio.mp3'")


                except:
                    return redirect('/error')
                
                translate=False
            
                
        return render_template('speech_translator.html',val=globalvarquery,res=globalvartt)
    except:
        return redirect('/error')

@app.route('/play_audio',methods=['GET', 'POST'])
def play_translated_audio():
    file_name = 'STS-TranslatedAudioFile.mp3'
    
    if os.path.exists(file_name):
        try:
            webbrowser.open(file_name)
            return redirect('/speech_translator1')
        except:
            return redirect('/error')
    else:
        return redirect('/error')  # Redirect to an error page if the file doesn't exist


@app.route('/download_document')
def download_document():
    try:
        document_path = 'STS-TranslatedAudioFile.mp3'
        send_file(document_path, as_attachment=True)
        os.remove(document_path)
        return 
    except:
        return redirect('/error')



#common
def save_audio_to_mp3(translated_text, to_lang,file_name='STS-TranslatedAudioFile.mp3'):
    tts = gTTS(translated_text, lang=to_lang)
    tts.save(file_name)
@app.route('/error', methods=['GET', 'POST'])
def error():
    return render_template('error.html')
@app.route('/play_error', methods=['GET', 'POST'])
def plerror():
    return render_template('plerror.html')



        

if __name__ == '__main__':
    try:
        app.run(debug=True)
    except:
        'An error occured due to invalid input'
