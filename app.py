import os
import sys
import json
import six
import requests
from Crypto.Cipher import DES
from Crypto import Random
from flask import Flask, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from pymessenger.bot import Bot

UPLOAD_FOLDER = 'tmp/'
ALLOWED_EXTENSIONS = set(['txt', 'png'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ACCESS_TOKEN = os.environ["PAGE_ACCESS_TOKEN"]
VERIFY_TOKEN = os.environ["VERIFY_TOKEN"]
key = ''
text = ''
flag = False
flag_llave = False
flag_hola = False
flag_encrypt = False
flag_decrypt = False
bot = Bot(ACCESS_TOKEN)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/tmp', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''

@app.route('/tmp/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)

@app.route('/', methods=['POST'])
def webhook():
    output = request.get_json()
    log(output)
    #upload_file()
    archivo = open('tmp/file.txt', 'r')
    contenido = archivo.read()
    logs("Texto archivo: " + contenido)
    archivo.close()
    if output["object"] == "page":

        for event in output["entry"]:
            messaging = event["messaging"]
            for x in messaging:
                if x.get("message"):
                    recipient_id = x['sender']['id']
                    if x['message'].get('text'):
                        message = x['message']['text']
                        if message == 'Hola':
                            bot.send_text_message(recipient_id, "Hi, I'm Crypt2me. Write a 8 characters key...")
                            set_flag(True)
                        elif message == "prueba":
                            send_file(recipient_id,'file.txt')
                        elif len(key) == 8 and message != 'clear':
                            EncryptDES(key,text,recipient_id)
                            set_text(message)
                            bot.send_text_message(recipient_id, 'message')
                            set_flag_encrypt(False)
                        elif message == "clear":
                            set_flag_llave(False)
                            set_flag_hola(False)
                            set_flag_encrypt(False)
                            set_flag_decrypt(False)
                            bot.send_text_message(recipient_id,'clearing')
                        elif len(message) != 8 and flag == True:
                            bot.send_text_message(recipient_id, 'The length of the key is diferent to 8 characters...')
                        elif len(message) == 8 and flag == True:
                            set_key(message)
                            send_menu(recipient_id, "What do you want to do next?...")
                        else:
                            pass
                    else:
                        pass
                elif x.get("postback"):
                    recipient_id = x['sender']['id']
                    postback = x["postback"]["payload"]
                    if postback == "Encrypt":
                        set_flag(False)
                        set_flag_encrypt(True)
                        bot.send_text_message(recipient_id, "Write the text that you want to encrypt...")
                    elif postback == "Decrypt":
                        set_flag(False)
                        set_flag_decrypt(True)
                        bot.send_text_message(recipient_id, 'Well done')
        return "Success"

def set_key(value):
    global key
    key = value

def set_text(value):
    global text
    text = value

def set_flag(value):
    global flag
    flag = value

def set_flag_llave(value):
    global flag_llave
    flag_llave = value

def set_flag_hola(value):
    global flag_hola
    flag_hola = value

def set_flag_encrypt(value):
    global flag_encrypt
    flag_encrypt = value

def set_flag_decrypt(value):
    global flag_decrypt
    flag_decrypt = value

def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()

def logs(message):  # simple wrapper for logging to stdout on heroku
    print message
    sys.stdout.flush()

def EncryptDES(key, text,recipient_id):
    logs("text: " + text)
    cipher = DES.new(key, DES.MODE_OFB, '12345678')
    with open(os.path.dirname(os.path.abspath(__file__)) + '/tmp/file.txt', 'w') as out_file:
            while True:
                if len(text) == 0:
                    break
                elif len(text) % 16 != 0:
                    text += ' ' * (16 - len(text) % 16)
                out_file.write(cipher.encrypt(text))
    bot.send_file(recipient_id, os.path.dirname(os.path.abspath(__file__)) + '/tmp/file.txt')

def send_file(recipient_id, files):
    log("sending file to {recipient} {files}".format(recipient=recipient_id, files=files))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient":{
        "id": recipient_id
        },
        "message":{
            "attachment":{
                "type":"file",
                "payload":{
                    "url":"https://afternoon-mountain-34766.herokuapp.com/tmp/" + files
                }
            }
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def send_menu(recipient_id, message_text):
    log("sending menu to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
        "id": recipient_id
        },
        "message":{
            "attachment":{
                "type":"template",
                "payload":{
                    "template_type":"button",
                    "text": message_text,
                    "buttons":[
                        {
                            "type":"postback",
                            "title":"Encrypt",
                            "payload":"Encrypt"
                        },
                        {
                            "type":"postback",
                            "title":"Decrypt",
                            "payload":"Decrypt"
                        }
                    ]
                }
            }
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

if __name__ == '__main__':
    app.run(debug=True)
