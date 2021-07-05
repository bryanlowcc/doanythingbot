# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

# Set env variable before importing transformers
import os
os.environ['XDG_CACHE_HOME'] = "/tmp/cache"

import requests

# This is a simple example for a custom action which utters "Hello World!"
from typing import Any, Text, Dict, List
from datetime import datetime

from rasa_sdk import Action, Tracker
from rasa_sdk.events import UserUtteranceReverted, SessionStarted, ActionExecuted, UserUttered
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

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # time = int(datetime.now().strftime("%H"))

        # if time >= 5 and time < 12:
        #     response = "Good Morning! How may I assist you today?"
        #     dispatcher.utter_message(text=response)

        # elif time >= 12 and time < 17:
        #     response = "Good Afternoon! How may I assist you today?"
        #     dispatcher.utter_message(text=response)

        # else:
        #     response = "Good Evening! How may I assist you today?"
        #     dispatcher.utter_message(text=response)
        # dispatcher.utter_message(text="type help for the list of features I'm currently capable of.")
        return [SessionStarted(), ActionExecuted("action_welcome"), UserUttered(text = "/session_start")]

class WelcomeMessage(Action):
    def name(self) -> Text:
        return "action_welcome"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        time = int(datetime.now().strftime("%H"))

        if time >= 5 and time < 12:
            response = "Good Morning! How may I assist you today?"
            dispatcher.utter_message(text=response)

        elif time >= 12 and time < 17:
            response = "Good Afternoon! How may I assist you today?"
            dispatcher.utter_message(text=response)

        else:
            response = "Good Evening! How may I assist you today?"
            dispatcher.utter_message(text=response)
        dispatcher.utter_message(text="type help for the list of features I'm currently capable of.")
        return []

class GeneralConvo(Action):
    def name(self) -> Text:
        return "action_convo"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        inputs = tokenizer([tracker.latest_message['text']], return_tensors='pt')
        reply_ids = model.generate(**inputs)
        dispatcher.utter_message(text="{}".format(tokenizer.batch_decode(reply_ids)[0].replace("<s>", "").replace("</s>", "")))

        return [UserUtteranceReverted()]

class TextGenerator(Action):
    def name(self) -> Text:
        return "action_gen_text"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        generated_text = generator(tracker.slots.get("text4gen"), min_length=30, max_length=200, num_return_sequences=1)[0].get("generated_text")
        dispatcher.utter_message(text=generated_text)

        return [UserUtteranceReverted()]

class Feedback(Action):
    def name(self) -> Text:
        return "action_feedback"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        feedback_sheet.insert_row([tracker.slots.get("text4feedback")], 1)
        dispatcher.utter_message(text="Your feedback has been submitted! Thank you.")

        return [UserUtteranceReverted()]

class Covid(Action):
    def name(self) -> Text:
        return "action_covid"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        stats_today = requests.get("https://disease.sh/v3/covid-19/countries/MY?strict=true").json()
        stats_yest = requests.get("https://disease.sh/v3/covid-19/countries/MY?yesterday=true&strict=true").json()

        if stats_today["todayCases"] == "0":
            cases_today = "N/A yet"
        else:
            cases_today = stats_today["todayCases"]
        cases_yest = stats_yest["todayCases"]
        total_cases = stats_today["cases"]
        total_deaths = stats_today["deaths"]
        total_pop = stats_today["population"]
        total_tests = stats_today["tests"]
        test_ratio = str(round(int(stats_today["testsPerOneMillion"])/10000)) + "/100"

        vax_data_str = requests.get("https://raw.githubusercontent.com/CITF-Malaysia/citf-public/main/vaccination/vax_malaysia.csv").text.splitlines()[-1]
        vax_data = ''.join(vax_data_str).split(",")
        vax1_today = vax_data[1]
        vax2_today = vax_data[2]
        total_vax1 = vax_data[4]
        total_vax2 = vax_data[5]

        response =  f"Here are the current covid statistics for Malaysia:\nNew cases today = {cases_today}\nNew cases yesterday = {cases_yest}\nCurrent total active cases = {total_cases}\nCurrent total deaths = {total_deaths}\nTotal population in Malaysia = {total_pop}\nTotal tests = {total_tests}\nTest ratio per 100 people: {test_ratio}\nNew 1st dose vaccinations today = {vax1_today}\nNew 2nd dose vaccinations today = {vax2_today}\nTotal 1st dose vaccinations = {total_vax1}\nTotal 2nd dose vaccinations = {total_vax2}"

        dispatcher.utter_message(text=response)
        # dispatcher.utter_message(text="Here are the current covid statistics for Malaysia:")
        # dispatcher.utter_message(text=f"New cases today = {cases_today}")
        # dispatcher.utter_message(text=f"New cases yesterday = {cases_yest}")
        # dispatcher.utter_message(text=f"Current total active cases = {total_cases}")
        # dispatcher.utter_message(text=f"Current total deaths = {total_deaths}")
        # dispatcher.utter_message(text=f"Total population in Malaysia = {total_pop}")
        # dispatcher.utter_message(text=f"Total tests = {total_tests}")
        # dispatcher.utter_message(text=f"Test ratio per 100 people: {test_ratio}")
        # dispatcher.utter_message(text=f"New 1st dose vaccinations today = {vax1_today}")
        # dispatcher.utter_message(text=f"New 2nd dose vaccinations today = {vax2_today}")
        # dispatcher.utter_message(text=f"Total 1st dose vaccinations = {total_vax1}")
        # dispatcher.utter_message(text=f"Total 2nd dose vaccinations = {total_vax2}")

        return [UserUtteranceReverted()]        