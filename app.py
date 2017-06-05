import os
import sys
import json
import six
from flask import Flask, request
from pymessenger.bot import Bot

app = Flask(__name__)

ACCESS_TOKEN = os.environ["PAGE_ACCESS_TOKEN"]
VERIFY_TOKEN = os.environ["VERIFY_TOKEN"]
flag_hola = False
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

@app.route('/', methods=['POST'])
def webhook():
    output = request.get_json()
    log(output)
    if output["object"] == "page":

        for event in output["entry"]:
            messaging = event["messaging"]
            for x in messaging:
                if x.get("message"):
                    recipient_id = x['sender']['id']
                    if x['message'].get('text'):
                        message = x['message']['text']
                        if message == 'Hola' and flag_hola == False:
                            bot.send_text_message(recipient_id, "Hi, I'm Crypt2me. Write a 8 characters key...")
                            set_flag_hola(True)
                        elif message == "clear":
                            bot.send_text_message(recipient_id,'clearing')
                            set_flag_hola(False)
                        elif len(message) != 8 and flag_hola == True:
                            bot.send_text_message(recipient_id, 'The length of the key is diferent to 8 characters...')
                            set_flag_hola(True)
                        elif len(message) == 8 and flag_hola == True:
                            elements = []
                            #element = Button(type="postback", title="Encrypt", payload="Encrypt")
                            #element = Button(type="postback", title="Decrypt", payload="Decrypt")
                            element = Element(title="test", image_url="<arsenal_logo.png>", subtitle="subtitle", item_url="https://pbs.twimg.com/profile_images/803175670595600384/3aGBQn3r_400x400.jpg")
                            elements.append(element)
                            bot.send_generic_message(recipient_id,elements)
                            #bot.send_text_message(recipient_id, 'Menu')
                            set_flag_hola(False)
                        else:
                            pass
                    else:
                        pass
        return "Success"


@app.route("/", methods=['GET', 'POST'])
def hello():
    if request.method == 'GET':
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        else:
            return 'Invalid verification token'

    if request.method == 'POST':
        output = request.get_json()
        for event in output['entry']:
            messaging = event['messaging']
            for x in messaging:
                if x.get('message'):
                    recipient_id = x['sender']['id']
                    if x['message'].get('text'):
                        message = x['message']['text']
                        bot.send_text_message(recipient_id, message)
                    if x['message'].get('attachments'):
                        for att in x['message'].get('attachments'):
                            bot.send_attachment_url(recipient_id, att['type'], att['payload']['url'])
                else:
                    pass
        return "Success"

def set_flag_hola(value):
    global flag_hola
    flag_hola = value

def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()

def logs(message):  # simple wrapper for logging to stdout on heroku
    print message
    sys.stdout.flush()

class Element(dict):
    __acceptable_keys = ['title', 'item_url', 'image_url', 'subtitle', 'buttons']

    def __init__(self, *args, **kwargs):
        if six.PY2:
            kwargs = {k: v for k, v in kwargs.iteritems() if k in self.__acceptable_keys}
        else:
            kwargs = {k: v for k, v in kwargs.items() if k in self.__acceptable_keys}
        super(Element, self).__init__(*args, **kwargs)

    def to_json(self):
        return json.dumps({k: v for k, v in self.iteritems() if k in self.__acceptable_keys})


class Button(dict):
    __acceptable_keys = ['type', 'title', 'payload']

    def __init__(self, *args, **kwargs):
        if six.PY2:
            kwargs = {k: v for k, v in kwargs.iteritems() if k in self.__acceptable_keys}
        else:
            kwargs = {k: v for k, v in kwargs.items() if k in self.__acceptable_keys}
        super(Element, self).__init__(*args, **kwargs)

    ef to_json(self):
        return json.dumps({k: v for k, v in self.iteritems() if k in self.__acceptable_keys})

if __name__ == '__main__':
    app.run(debug=True)
