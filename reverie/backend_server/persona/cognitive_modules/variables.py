verbose_reflection = False
verbose_prompts = False
verbose_movements = True
INTERVIEW_SECTOR = "Home"
INTERVIEW_ARENA = "Living Room"
CHAT_SIMULATION_STEPS = 5
import re
import time
import pandas as pd
import json
from typing import List, Dict, Any
from openai import OpenAI
import random
import numpy as np
import math
# Copy and paste your OpenAI API Key
openai_api_key = ""
# Put your name
key_owner = ""

class NavelEmotion:
    emo_map = {
            "neutral": [],
            "happy": ["Joy", "Love", "Gratification","Hope", "Admiration" ],
            "sad": ["Remorse", "Fears-confirmed", "Disappointment", "Sorry-for", "Shame"],
            "surprise": ["Distress",  "Fear", "Relief"],
            "anger": ["Hate", "Resentment", "Anger", "Reproach"],
            "smile": ["Happy-for", "Pride", "Gloating","Satisfaction", "Gratitude"],
        }
    
    emo = {"neutral": 0,
    "happy": 0,
    "sad": 0,
    "surprise": 0,
    "anger": 0,
    "smile": 0,}
    
    

    def set_em_from_OCC(self, em, value):
        em_navel = self.get_navel_emotion(em, value)
        self.set_em_from_navel(em_navel, value)

    def set_from_participant_info(self, par_info):

        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", par_info)

        # Convert to float
        numbers = [float(num) for num in numbers]

        i = 0
        if len(numbers)>0:
                for k in self.emo.keys():
                    try:    
                        self.emo[k] = numbers[i]
                        i+=1
                    except Exception:
                        continue
        return self



    def set_em_from_navel(self,em_navel,value):
        self.emo.update({em_navel:value})

    def get_navel_emotion(self, em, em_value):
            
        if em_value <= 0.2:
            return "neutral"
        keys = self.emo_map.keys()
        adm_choices = ["happy", "smile"]
        if em == "Admiration":
            c = random.choice(adm_choices)
            print(c)
            return c

        for k in keys:
            if em in self.emo_map.get(k):
                return k
        return "random"
    
    def __repr__(self):
        return f"NavelEmotion:(neutral: {self.neutral};happy: {self.happy};sad: {self.sad};surprise: {self.surprise};anger: {self.anger};smile: {self.smile})"
    
    def get_major_emotion(self):

        # Get the key with the maximum value
        max_key = max(self.emo, key=self.emo.get)

        # Get the maximum value
        max_value = self.emo[max_key]

        return max_key, max_value
    



class ExperimentData:
    def __init__(self):
        self.columns = ["timestamp",
            "preparing_time", "response_time", "appraisal_time", "main_emotion_OCC", "user_emotion_OCC", "input", "response",
            "navel_neutral", "navel_happy", "navel_sad", "navel_surprise", "navel_anger", "navel_smile",
            "gaze_x", "gaze_y", "gaze_z", "gaze_overlap"
        ]
        self.data = pd.DataFrame(columns=self.columns)

    def add_entry(self, t, preparing_time: float, response_time: float, appraisal_time: float,
                  emotion: str, user_emotion:str, input_text: str, response_text: str,
                  navel_emotion: List[float], gaze_vector: List[float], gaze_overlap: float):
        """Adds a new entry to the experiment dataset."""
        if len(navel_emotion) != 6:
            raise ValueError("navel_emotion must be a list of 6 float values.")
        if len(gaze_vector) != 3:
            raise ValueError("gaze_vector must be a list of 3 float values.")

        new_entry = {
            "timestamp":t,
            "preparing_time": preparing_time,
            "response_time": response_time,
            "appraisal_time": appraisal_time,
            "main_emotion_OCC": emotion,
            "user_emotion_OCC": user_emotion,
            "input": input_text,
            "response": response_text,
            "navel_neutral": navel_emotion[0],
            "navel_happy": navel_emotion[1],
            "navel_sad": navel_emotion[2],
            "navel_surprise": navel_emotion[3],
            "navel_anger": navel_emotion[4],
            "navel_smile": navel_emotion[5],
            "gaze_x": gaze_vector[0],
            "gaze_y": gaze_vector[1],
            "gaze_z": gaze_vector[2],
            "gaze_overlap": gaze_overlap,
            "input_length": len(input_text.split()),
            "response_length": len(response_text.split()),
            "input_sentiment": None,
            "response_sentiment": None,
        }
        self.data = pd.concat([self.data, pd.DataFrame([new_entry])], ignore_index=True)

    def add_entry(self, t, preparing_time: float, response_time: float, appraisal_time: float,
                  emotion: str,user_emotion:str, input_text: str, response_text: str,
                  par:str):
        """Adds a new entry to the experiment dataset."""

        if input_text is not None:
            input_text = input_text.strip().strip("\"")
        if response_text is not None:
            response_text = response_text.strip().strip("\"")
       
        navel_emotion_pattern = r"Participant Info\s*:\s*\(\s*CartVec3d\(\s*x=([-\d\.]+)\s*\,\s*y=([-\d\.]+)\s*\,\s*z=([-\d\.]+)\)\s*\,\s*([\d\.]+)\s*\,\s*PersonFacialExpression\(neutral\s*=\s*([\d\.]+)\s*,\s*happy\s*=\s*([\d\.]+)\s*,\s*sad\s*=\s*([\d\.]+)\s*,\s*surprise\s*=\s*([\d\.]+)\s*,\s*anger\s*=\s*([\d\.]+)(\s*,\s*smile\s*=\s*([\d\.]+))?\)\s*\)"

        try:
            in_len = len(input_text.split())
        except Exception as e:
            in_len = None

        try:
            resp_len = len(response_text.split())
        except Exception as e:
            resp_len = None
        

        
            #print("CONTENT = " + str(content))
        try:    
            navel_emotions = re.findall(navel_emotion_pattern, par)[0]
            print(navel_emotions)

            overlap = navel_emotions[3]
            neutral =  navel_emotions[4]
            happy =  navel_emotions[5]
            sad =  navel_emotions[6]
            surprise=  navel_emotions[7]
            anger=  navel_emotions[8]
            x= navel_emotions[0]
            y= navel_emotions[1]
            z= navel_emotions[2]



            
        except Exception as e:
            neutral = None
            happy =  None
            sad =  None
            surprise=  None
            anger=  None
            x= None
            y= None
            z= None
            overlap =None
            print("ERRO CARAMBAS = " + str(e))

        try:
            navel_emotions = re.findall(navel_emotion_pattern, par)
            smile=  navel_emotions[9]
        except:
            smile = None


            new_entry = {
                "timestamp": t,
                "preparing_time": preparing_time,
                "response_time": response_time,
                "appraisal_time": appraisal_time,
                "main_emotion_OCC": emotion,
                "user_emotion_OCC":user_emotion,
                "input": input_text,
                "response": response_text,
                "navel_neutral": neutral,
                "navel_happy": happy,
                "navel_sad": sad,
                "navel_surprise": surprise,
                "navel_anger": anger,
                "navel_smile": smile,
                "gaze_x": x,
                "gaze_y": y,
                "gaze_z": z,
                "gaze_overlap": overlap,
                "input_length": in_len,
                "response_length": resp_len,
                "input_sentiment": None,
                "response_sentiment": None,
            }
        #print(new_entry)
        self.data = pd.concat([self.data, pd.DataFrame([new_entry])], ignore_index=True)

    def save_to_csv(self, filename: str):
        """Saves the experiment data to a CSV file."""
        self.data.to_csv(filename, index=False, na_rep="null")

    def save_to_json(self, filename: str):
        """Saves the experiment data to a JSON file."""
        self.data.to_json(filename, orient="records", indent=4)

    def load_from_csv(self, filename: str):
        """Loads experiment data from a CSV file."""
        self.data = pd.read_csv(filename)
        return self

    def load_from_json(self, filename: str):
        """Loads experiment data from a JSON file."""
        self.data = pd.read_json(filename, orient="records")

    def get_data(self) -> pd.DataFrame:
        """Returns the stored data as a Pandas DataFrame."""
        return self.data
    
    def extract_experiment_data(self, log_file):
        # Define regex patterns
        time_pattern = r"TIME\s*:\s*(.*)\n"
        input_pattern = r"INPUT\s*:\s*(.*)\n"
        response_pattern = r"RESPONSE\s*:\s*(.*)\n"
        preparing_time_pattern = r"PREPARING TAKES\s*=\s*([\d\.]+)\n"
        response_time_pattern = r"GENERATING TAKES\s*=\s*([\d\.]+)\n"
        appraisal_time_pattern = r"APPRAISAL TOOK:\s*([\d\.]+).*\n"
        emotion_pattern = r"MAIN EMOTION\s*=\s*(.*)\s*\:\s*([\d\.]+).*\n"
        user_emotion_pattern = r"USER EMOTION\s*=\s*(.*)\s*\:\s*([\d\.]+).*\n"

        navel_emotion_pattern = r"Participant Info\s*:\s*\(\s*CartVec3d\(\s*x=([-\d\.]+)\s*\,\s*y=([-\d\.]+)\s*\,\s*z=([-\d\.]+)\)\s*\,\s*([\d\.]+)\s*\,\s*PersonFacialExpression\(neutral\s*=\s*([\d\.]+)\s*,\s*happy\s*=\s*([\d\.]+)\s*,\s*sad\s*=\s*([\d\.]+)\s*,\s*surprise\s*=\s*([\d\.]+)\s*,\s*anger\s*=\s*([\d\.]+)(\s*,\s*smile\s*=\s*([\d\.]+))?\)\s*\)"

        # Storage for extracted data
        data = []

        with open(log_file, 'r', encoding='utf-8') as file:
            content = file.read()
            #print("CONTENT = " + str(content))

        # Find all matches
        time = re.findall(time_pattern, content)

        inputs = re.findall(input_pattern, content)
        #print(inputs)
        responses = re.findall(response_pattern, content)
        #print(responses)
        preparing_times = re.findall(preparing_time_pattern, content)
        #print(preparing_times)
        response_times = re.findall(response_time_pattern, content)
        #print(response_times)
        appraisal_times = re.findall(appraisal_time_pattern, content)
        #print(appraisal_times)
        emotions = re.findall(emotion_pattern, content)
        #print(emotions)
        user_emotions = re.findall(user_emotion_pattern, content)
        #print(user_emotions)
        navel_emotions = re.findall(navel_emotion_pattern, content)
        #print(navel_emotions)

        # Convert to appropriate types
        num_entries = max(len(inputs), len(responses), len(preparing_times), len(response_times), 
                        len(appraisal_times),len(user_emotions), len(navel_emotions), len(emotions))
        
        #print(num_entries)

        for i in range(num_entries):
            try:
                smile = float(navel_emotions[i][10])
            except Exception:
                smile = None
            
            try:
                prep = float(preparing_times[i])
            except Exception:
                prep = None
            try:
                resp_t = float(response_times[i])
            except Exception:
                resp_t = None
            try:
                app = float(appraisal_times[i])
            except Exception:
                app = None
            
            try:
                ems = str(emotions[i])
            except Exception:
                ems = None
            try:
                user_ems = str(user_emotions[i])
            except Exception:
                user_ems = None
            try:
                inp = float(inputs[i])
            except Exception:
                inp = None
            try:
                resp = responses[i]
            except Exception:
                resp = None

            try:
                navel_neutral = float(navel_emotions[i][4])
            except Exception:
                navel_neutral = None
            try:
                navel_happy = float(navel_emotions[i][5])
            except Exception:
                navel_happy = None
            try:
                navel_sad = float(navel_emotions[i][6])
            except Exception:
                navel_sad = None

            try:
                navel_surprise = float(navel_emotions[i][7])
            except Exception:
                navel_surprise = None
            try:
                navel_anger = float(navel_emotions[i][8])
            except Exception:
                navel_anger = None
            try:
                overlap = float(navel_emotions[i][3])
            except Exception:
                overlap = None

            try:
                x = float(navel_emotions[i][0])
            except Exception:
                x = None
            try:
                y = float(navel_emotions[i][1])
            except Exception:
                y = None
            try:
                z = float(navel_emotions[i][2])
            except Exception:
                z = None

            try:
                leng = len(inputs[i].split())
            except Exception:
                leng = None
            try:
                resp_leng = len(responses[i].split())
            except Exception:
                resp_leng = None
            




            row = {
                "timestamp": time,
                "preparing_time": prep,
                "response_time": resp_t,
                "appraisal_time": app,
                "main_emotion_OCC": ems,  # Extract emotion string
                "user_emotion_OCC": user_ems,
                "input": inp,
                "response": resp,
                "navel_neutral": navel_neutral,
                "navel_happy": navel_happy,
                "navel_sad": navel_sad,
                "navel_surprise": navel_surprise,
                "navel_anger": navel_anger,
                "navel_smile": smile,
                "gaze_overlap": overlap,
                "gaze_x": x,
                "gaze_y": y,
                "gaze_z": z,
                "input_length": leng,
                "response_length": resp_leng,
                "input_sentiment": None,
                "response_sentiment": None,
            }
            self.data = pd.concat([self.data, pd.DataFrame([row])], ignore_index=True)

    def parse_analysis(self, input_analysis):
        if "neutral" in input_analysis:
            input_analysis = 0
        elif "positive" in input_analysis:
            input_analysis = 1
        elif "negative" in input_analysis:
            input_analysis = -1
        else:
            return None
        return input_analysis


    def analyze_sentiment(self):
        """Uses GPT-4o mini to analyze sentiment for input and response fields."""
        client = OpenAI(api_key=openai_api_key)

        for i, row in self.data.iterrows():
            input_text = row["input"]
            response_text = row["response"]

            try:
               
                test = (math.isnan(input_text) == False and math.isnan(response_text) == False)
                self.data.at[i, "input_sentiment"] = float("nan")
                self.data.at[i, "response_sentiment"] = float("nan")
            except Exception as e1:
                
            
                prompt = f"""Analyze the sentiment of the following texts:\n\nInput: {input_text}\nResponse: {response_text}\n\nProvide a sentiment label (Positive, Neutral, Negative) for each.
                Respond in the following format:
                Input Analysis: an explanation of your reasoning.
                Input: (one of positive, neutral, or negative)
                Response Analysis: an explanation of your reasoning.
                Response: (one of positive, neutral, or negative)
                """
                
                try:
                    inp = "neutral"
                    resp = "neutral"
                    for j in range(5):

                        completion = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "system", "content": "You are a helpful assistant."},
                                    {"role": "user", "content": prompt}]
                        )
                        
                        sentiment_output = completion.choices[0].message.content.strip()
                        #print(sentiment_output)
                        sentiments = sentiment_output
                        
                        input_analysis = sentiments.split("Input: ")[-1].split("\n")[0].strip().lower()
                        response_analysis = sentiments.split("Response: ")[-1].split("\n")[0].strip().lower()
                        #print("in = " + str(input_analysis))
                        #print("resp = " + str(response_analysis))
                        input_analysis = self.parse_analysis(input_analysis)
                        response_analysis = self.parse_analysis(response_analysis)
                        if input_analysis is not None and response_analysis is not None:
                            inp = input_analysis
                            resp = response_analysis
                            break
                        
                    self.data.at[i, "input_sentiment"] = inp
                    self.data.at[i, "response_sentiment"] = resp
                    #print("FINAL INP = " + str(inp))
                    #print("FINAL RESP = " + str(resp))
                except Exception as e:
                    #print(f"Error analyzing sentiment: {e}")
                    self.data.at[i, "input_sentiment"] = float("nan")
                    self.data.at[i, "response_sentiment"] = float("nan")
                


        





# Example usage
if __name__ == "__main__":
    experiment = ExperimentData()
    experiment.extract_experiment_data("logs/log.json")
    experiment.analyze_sentiment()


    experiment.save_to_csv("experiment_data.csv")
    experiment.save_to_json("experiment_data.json")
    
    # Load data back
    experiment.load_from_csv("experiment_data.csv")
    print(experiment.get_data())
