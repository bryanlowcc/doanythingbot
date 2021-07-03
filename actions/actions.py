# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

# Set env variable before importing transformers
import os
os.environ['XDG_CACHE_HOME'] = "/tmp/cache"

# This is a simple example for a custom action which utters "Hello World!"
from typing import Any, Text, Dict, List
from datetime import datetime

from rasa_sdk import Action, Tracker
from rasa_sdk.events import UserUtteranceReverted, SessionStarted, ActionExecuted, SlotSet
from rasa_sdk.executor import CollectingDispatcher

# For general conversation using BlenderBot in Fallback policy
from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration, pipeline, set_seed
model = BlenderbotForConditionalGeneration.from_pretrained('facebook/blenderbot-400M-distill')
tokenizer = BlenderbotTokenizer.from_pretrained('facebook/blenderbot-400M-distill')
generator = pipeline('text-generation', model='gpt2')
set_seed(42)

# For storing feedback in Google Sheets
from oauth2client.service_account import ServiceAccountCredentials
import gspread
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('actions/doanythingbot-sheetkey-87f175724514.json', scope)
client = gspread.authorize(creds)
feedback_sheet = client.open("doanythingbot-feedback").worksheet('feedback')

class ActionSessionStart(Action):
    def name(self) -> Text:
        return "action_session_start"

    async def run(
      self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # time = int(datetime.now().strftime("%H"))

        # if time >= 5 and time < 12:
        #     response = "Good Morning! How may I assist you today?\ntype help for the list of features I'm currently capable of"
        #     dispatcher.utter_message(text=response)

        # elif time >= 12 and time < 17:
        #     response = "Good Afternoon! How may I assist you today?\ntype help for the list of features I'm currently capable of"
        #     dispatcher.utter_message(text=response)

        # else:
        #     response = "Good Evening! How may I assist you today?\ntype help for the list of features I'm currently capable of"
        #     dispatcher.utter_message(text=response)
        return [SessionStarted(), ActionExecuted("action_welcome"), ActionExecuted("action_listen")]

class WelcomeMessage(Action):
    def name(self) -> Text:
        return "action_welcome"

    async def run(self, dispatcher: CollectingDispatcher,tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        time = int(datetime.now().strftime("%H"))

        if time >= 5 and time < 12:
            response = "Good Morning! How may I assist you today?\ntype help for the list of features I'm currently capable of"
            dispatcher.utter_message(text=response)

        elif time >= 12 and time < 17:
            response = "Good Afternoon! How may I assist you today?\ntype help for the list of features I'm currently capable of"
            dispatcher.utter_message(text=response)

        else:
            response = "Good Evening! How may I assist you today?\ntype help for the list of features I'm currently capable of"
            dispatcher.utter_message(text=response)

        return []

class GeneralConvo(Action):
    def name(self) -> Text:
        return "action_convo"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        inputs = tokenizer([tracker.latest_message['text']], return_tensors='pt')
        print(tracker.latest_message['text'] + " " + str(inputs))
        reply_ids = model.generate(**inputs)
        dispatcher.utter_message(text="{}".format(tokenizer.batch_decode(reply_ids)[0].replace("<s>", "").replace("</s>", "")))

        # Revert user message which led to fallback.
        return [UserUtteranceReverted()]

class TextGenerator(Action):
    def name(self) -> Text:
        return "action_gen_text"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        generated_text = generator(tracker.slots.get("text4gen"), min_length=30, max_length=200, num_return_sequences=1)[0].get("generated_text").replace("\n\n", "\n")
        dispatcher.utter_message(text=generated_text)

        return [UserUtteranceReverted()]

class Feedback(Action):
    def name(self) -> Text:
        return "action_feedback"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        feedback_sheet.insert_row([tracker.slots.get("text4feedback")], 1)
        dispatcher.utter_message(text="Your feedback has been submitted! Thank you.")

        return [UserUtteranceReverted()]