import os
import sys
import json
from Crypto.Cipher import DES
from Crypto import Random

import requests
from flask import Flask, request

flag = False

app = Flask(__name__)

def EncryptDES(key, text):
    print "aqui"
    cipher = DES.new(key, DES.MODE_OFB, '12345678')
    while True:
        if len(text) == 0:
            break
        elif len(text) % 16 != 0:
            text += ' ' * (16 - len(text) % 16)
        ciphertext = cipher.encrypt(text)
    flag = False
    return ciphertext


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    key = ""
    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text
                    if message_text ==  "Hola":
                        send_message(sender_id, "Hi, I'm Crypt2me. Write a 8 byte key...")
                    elif len(message_text) == 8:
                        key = message_text
                        send_menu(sender_id, "What do you want to do next?")
                    elif message_text ==  "Adios":
                        send_message(sender_id, "Di Adios")
                    elif (key != "" and message_text != "" and flag == True):
                        text = message_text
                        send_message(sender_id, EncryptDES(key,text,flag))


                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message

                    sender_id = messaging_event["sender"]["id"]
                    respuesta = messaging_event["postback"]["payload"]
                    if respuesta == "Encrypt":
                        send_message(sender_id, "Write the text that you want to encrypt...")
                        flag = True
                    elif message_text == "Decrypt":
                        send_message(sender_id,"Kyc")
    return "ok", 200

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

def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

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
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()

def logs(message):  # simple wrapper for logging to stdout on heroku
    print "este" + str(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
