# soundtrigger.py

from twilio.rest import Client
from config import *


def SoundDetection(text):
    config = load_json('config.json')
    trigger_words_values = config['user_made_sounds']['trigger_words'].values()
    sound_pattern_values = config['user_made_sounds']['sound_pattern'].values()
    if any(value in text for value in trigger_words_values) or any(value in text for value in sound_pattern_values):
        return 1
    elif "stop" in text:
        return 2
    else:
        return 0


# This code is adapted from https://www.twilio.com/docs/libraries/python
def SoundTriggering(signal):
    if signal == 1:
        twilio_details = load_json('twilio_account_details.json')
        account_sid = twilio_details['account_sid']
        auth_token = twilio_details['auth_token']
        twilio_number = twilio_details['twilio_number']
        my_phone_number = twilio_details['my_phone_number']

        client = Client(account_sid, auth_token)

        message = client.messages.create(
            body="I need help!",
            from_=twilio_number,
            to=my_phone_number
        )
        print(message)
    else:
        return
    return
