import sys
sys.path.append('../../')

from global_methods import *
from reverie.backend_server.persona.cognitive_modules.occ import OCCModel
import json
from colorama import Fore, Style
from math import exp
from persona.prompt_template.run_gpt_prompt import run_gpt_emotional_reaction, run_gpt_prompt_generate_next_convo_emotional_reaction, run_gpt_coping_activation_conditions
from multiprocessing import Process, Queue, Manager
import datetime
import time
import numpy as np
import re

# Steepened Logarithmic function that never exceeds 10
def log_bounded_steep(x, K=1000, p=1.5):  # K controls approach speed, p controls steepness
    c = np.log(K)
    return 10 * ((np.log(x + 1))**p / ((np.log(x + 1))**p + c))




class CopingStrategy:
    def __init__(self, t_p, name, activation_condition, description):
        self.type = t_p
        self.name = name
        self.activation_condition = activation_condition
        self.description = description
        self.upper_limit = 10

    # Choose a coping strategy based on the dominant emotion
    def apply_strategy(self, emotion):
        strategy = ""
        return strategy
    
    def __str__(self):
        return "| " + str(self.name) + " |"

class EmotionalLayer:

    def __init__(self, name, emotional_map, emotional_layer, last_update):
        em_map, em_layer = {}, {}
        if check_if_file_exists(emotional_map): 
            # If we have a bootstrap file, load that here. 
            em_map = json.load(open(emotional_map))

            if check_if_file_exists(emotional_layer): 
            # If we have a bootstrap file, load that here. 
                em_layer = json.load(open(emotional_layer))
        self.mood = ("positive", 0)
        self.mood_threshold = 3
        self.OCC = OCCModel(em_map, em_layer)
        self.retain_hopes_and_fears = 3
        self.last_update = last_update
        self.focused_event = False
        self.name = name
        self.event_triplet = None
        self.appraisals = None
        self.live_constant = None
        self.recency_multiplier_finished_events = 0.3
        self.recency_multiplier_ongoing_events = 0.5




        self.coping_strategies = {
            "Planning": CopingStrategy("Problem-Focused", "Planning", "Possible future event has desirable effect (facilitates desired state or inhibits undesired state)", "Develop plans to remove stressor."), 
            "Acceptance": CopingStrategy("Emotion-Focused", "Acceptance","An intended future state (i.e. a goal) seems unachievable (e.g., no viable plan exists)", "Accept stressor as real. Live with it."), 
            "Positive reinterpretation" : CopingStrategy("Emotion-Focused","Positive reinterpretation", "Past event or intended future event with undesirable effect has desirable side-effect", "Look for silver lining."),
            "Mental disengagement": CopingStrategy("Emotion-Focused", "Mental disengagement", "Desired goal seems unachievable", "Use other activities to take mind off problem: daydreaming, sleeping"),
            "Denial" : CopingStrategy("Emotion-Focused", "Denial", "Effect of past event or intended future event has undesirable effect", "Denying the reality of event."),
            "Shift Blame" : CopingStrategy("Emotion-Focused", "Shift Blame", "Event has undesirable effect and ambiguous causal attribution", "Blame for undesired event gets shifted to another cause.")
        }
        #self.print_layer()


    def get_coping_strategy(self, predominant_emotion, persona):

        # in the future a persona might have a probability associated with each coping strategy 
        # that's dependent on their own traits and personality, but for now, all have the same distribution
        
        activated_strategies = run_gpt_coping_activation_conditions( predominant_emotion, persona)[0]
        if len(activated_strategies) != 0:

            final_strat = random.choice(activated_strategies)

            print("FINAL STRAT = " + str(final_strat))

            if final_strat != len(self.coping_strategies.keys()):

                final_strat_key = list(self.coping_strategies.keys())[final_strat]

                coping_strat = self.coping_strategies.get(final_strat_key)

                if coping_strat:
                    return coping_strat
        return None


    def is_reaction_required(self):
        if self.focused_event:
            event = self.focused_event[1]["curr_event"]
            ##print("SHHSHSHS= " + str(type(event))+": "+ str(event))
            emotion = self.find_emotion_by_event(event)
            if emotion is not None:
                if emotion.value >= emotion.high_threshold:
                    return True
        return False

    def get_reaction(self, persona):
        act_desc, act_dura = None, None
        
        if self.focused_event:
            event = self.focused_event
            emotion = self.find_emotion_by_event(event[1]["curr_event"])
            if emotion is not None:
                if emotion.value >= emotion.high_threshold:
                    # change this prompt to include the specific emotion and not just the mood
                    # also the action tendencies?    
                    return run_gpt_emotional_reaction(persona, event, emotion, self.mood)[0]
        return (None, None)
    
    def get_conversation_emotional_reaction(self, persona):
    
        emotion = self.find_predominant_emotions(1)[0]
        if emotion is not None:
            #print("EMOTION = " + str(emotion))
            if emotion.value >= emotion.high_threshold:
                tendency = emotion.action_tendency
                em_state = f"{persona.name} is overwhelmed with feelings of {emotion.name}. In these situations {persona.name} has a tendency to {tendency}. Give me a reactive line of dialogue that encompasses this tendency."
                return em_state
        return ""
    

    
    def get_reaction_convo(self, persona, persona_name, curr_chat, summarized_idea):
        #print("BEFORE")
        #for elem in self.OCC.emotions:
            #print(elem)
        emotion = self.find_predominant_emotions(1)[0]
        #print("AFTER")
        #for elem in self.OCC.emotions:
            #print(elem)

        if emotion is not None:
            if emotion.value >= emotion.high_threshold:
                # change this prompt to include the specific emotion and not just the mood
                # also the action tendencies?    
                return run_gpt_prompt_generate_next_convo_emotional_reaction(persona, persona_name, curr_chat, summarized_idea, emotion)
        return None

    def find_most_intense_event(self):
        ev = None
        contrs = []
        for elem in self.OCC.emotions:
            sorted = elem.contributions.sort(key= lambda cont:cont[1], reverse=True)
            contrs.append(sorted[0])
        contrs.sort(key= lambda cont:cont[1], reverse=True)
        return contrs[0]
    
    # chnage function name and refactor later please - this is find emotion by event, not most intense
    def find_emotion_by_event(self, event):

        if event:
            p_event = event.subject, event.predicate, event.object

            for em in self.OCC.emotions:
                contrs = [ev for ev in em.contributions if (ev[0][0], ev[0][1], ev[0][2]) == p_event]
                if len(contrs)>0:
                    return em
        return None
    
    def find_predominant_emotions(self, amount):
        self.OCC.emotions.sort(key = lambda em: em.value, reverse=True)

        ems = self.OCC.emotions[:amount]
        #print("EMS = " + str(ems))
        return ems
        


    def save(self, folder):

        layer = dict()

        for emotion in self.OCC.emotions:
            layer.update({emotion.name:emotion.contributions})
        #print(layer)
        with open(folder, "w") as outfile:
            json.dump(layer, outfile, indent=2) 




    def get_str_hopes_and_fears(self, agent):
        hopes = self.OCC.find_emotion("Hope").contributions
        fears = self.OCC.find_emotion("Fear").contributions
        str = ""

        if hopes:
            hopes.sort(key=lambda hope: hope[1], reverse=True)
            for i in range(min(len(hopes), self.retain_hopes_and_fears)):
                elem = hopes[i]
                event = elem[0]
                intensity = elem[1]
                reason = elem[2]
                str+= f"""\nGiven the event: "{event}", {agent.name} felt hope, because: {reason}"""

        if fears:
            fears.sort(key=lambda fears: fears[1])
            for i in range(min(len(fears), self.retain_hopes_and_fears)):
                elem = fears[i]
                event = elem[0]
                intensity = elem[1]
                reason = elem[2]
            str+= f"""\nGiven the event: "{event}", {agent.name} felt fear, because: {reason}"""
        if len(hopes)==0 and len(fears)==0:
            str = f"{agent.name} has felt no hopes and fears as of yet."
        ##print("FEARS AND HOPES = "+ str)
        return str
    
    def update_contrib_decay(self, t_time):
        #print("T_TIME = " + str(t_time))
        #print("LAST UPDATE = " + str(self.last_update))
        for j in range(len(self.OCC.emotions)):
            #print("EMOTION = " + str(em))
            #print("LAST UPDATE = " + str(self.last_update))

            ind_emotion = j
            em = self.OCC.emotions[j]
            self.OCC.emotions[ind_emotion].value = 0
            if self.last_update is None:
                current_decay = 1
            else:
                time_delta = t_time-self.last_update
                #print("TIME DELTA = " + str(time_delta.total_seconds()))
                #print("EM DECAY = " + str(em.decay))
                live = self.live_constant
                if live == None:
                    live = 1

                current_decay = exp((-em.decay)* live * time_delta.total_seconds())
            contrs_to_remove = []
            #print("curr decay = " + str(current_decay))
            #print("BEF DECAY = " + str(self.OCC.emotions[ind_emotion].contributions))

            for i in range(len(em.contributions)):
                elem = em.contributions[i]
                #print("ELEM = " + str(elem))

                if ((elem[1] * current_decay)) >=em.low_threshold:
                    self.OCC.emotions[ind_emotion].contributions[i][1] *= current_decay
                    #self.OCC.emotions[ind_emotion].contributions[i][1] *=2
                else:
                    contrs_to_remove.append(elem)

            #print("AFETR DECAY = " + str(self.OCC.emotions[ind_emotion].contributions))
            
            for contr in contrs_to_remove:
                try:
                    ind = self.OCC.emotions[ind_emotion].contributions.index(contr)
                    self.OCC.emotions[ind_emotion].contributions.pop(ind)
                except ValueError:
                    print("Contribution "+ str(contr)+ "not in " + str(em.name)+ "'s contribution list")
            #print("Value")
        #print("LAYER DEPOIS DE UPDATE = ")
        #self.print_layer()
        self.last_update = t_time

    

    def update(self, appraisals, t_time, persona):
        #print(appraisals)

        #for i in range(len(self.OCC.emotions)):
            #self.OCC.emotions[i].value = 0

        
        if appraisals is not None:
            while len(appraisals)>0:
                appr = appraisals[len(appraisals)-1]
                #{"event": event, "reason": reason, "emotion" : emotion.name, "category" : emotion.category, "valence" : emotion.valence, "intensity":intensity}
                emotion_name = appr.get("emotion")
                emotion = self.OCC.find_emotion(emotion_name)
                intensity = appr.get("intensity")
                target = appr.get("target")
                #print("EVENT = " + str(appr.get("event")) + " | intensity: " +str(intensity))
                #print("LOW T = " + str(emotion.low_threshold))
                #print(appr)

                if intensity >= emotion.low_threshold:
                    event = appr.get("event")
                    reason = appr.get("reason")
                    #emotion.value += (intensity*0.1)

                    contrib_index = self.find_contributions(emotion, event)
                    if contrib_index == None:
                        emotion.contributions.append([event, intensity, reason, target])
                    else:
                        # contributions tupple: (event, intensity, reason, target) so we are modifying the intensity
                        # with 50% of the old value and 50% of the new
                        old_int = emotion.contributions[contrib_index][1]
                        emotion.contributions[contrib_index][1] = old_int * 0.5 + intensity *0.5
                
                        # maybe we can update the reason?
                appraisals.pop(len(appraisals)-1)

            joy = self.OCC.find_emotion("Joy")
            distress = self.OCC.find_emotion("Distress")
            pride = self.OCC.find_emotion("Pride")
            shame = self.OCC.find_emotion("Shame")
            admiration = self.OCC.find_emotion("Admiration")
            reproach = self.OCC.find_emotion("Reproach")

            #if joy.low_threshold <= joy.value:
                #if pride.low_threshold <= pride.value:
            gratification = self.OCC.find_emotion("Gratification")
            #gratification.value += joy.value * 0.5 + pride.value * 0.5
            gratification.contributions = joy.contributions + pride.contributions
                
                #if admiration.low_threshold <= admiration.value:
            gratitude = self.OCC.find_emotion("Gratitude")
            #gratitude.value += joy.value * 0.5 + admiration.value * 0.5
            gratitude.contributions = joy.contributions + admiration.contributions

            #if distress.low_threshold <= distress.value:
                #if shame.low_threshold <= shame.value:
            remorse = self.OCC.find_emotion("Remorse")
            #remorse.value += distress.value * 0.5 + shame.value * 0.5
            remorse.contributions = distress.contributions + shame.contributions
                
                #if reproach.low_threshold <= reproach.value:
            anger = self.OCC.find_emotion("Anger")
            #anger.value += distress.value * 0.5 + reproach.value * 0.5
            anger.contributions = distress.contributions + reproach.contributions

            self.update_contrib_decay(t_time)
            self.calculate_all_emotion_values(persona)
            self.update_mood()
            #print("AFTER UPDATE")
            
            #self.print_layer()


    def update_mood(self):
        
        final = 0

        for em in self.OCC.emotions:
            if em.valence.lower() == "negative":
                final-= em.value
            else:
                final+=em.value 
            

        
        
        if final>0:
            self.mood = ("positive", min(abs(final),20))
        else:
            self.mood = ("negative", min(abs(final), 20))
        value = 0
        for i in range(len(self.OCC.emotions)):
            emotion = self.OCC.emotions[i]

            if emotion.valence.lower() == self.mood[0].lower():
                #there are 22 emotions on the OCC model, 
                #so we give a bump to all emotions 
                # that have the same valence as the general mood
                # that bumb is 1/22 OCC emotions x mood
                value = (self.mood[1] * 1/len(self.OCC.emotions))
            else:
            
                value = -(self.mood[1] * 1/len(self.OCC.emotions))
            self.OCC.emotions[i].value += value
            #print("BOOOOOOST = " + str(value))


    def find_contributions(self, emotion, event):
        for i in range(len(emotion.contributions)):
            elem = emotion.contributions[i]
            if event == elem[0]:
                return i
        return None
    
    def trim_contribs(self, persona):
        for em in self.OCC.emotions:
            ##print("EM CONTRS Before = " + str(em.name)+ " : " + str(em.contributions))
            #persona.scratch.retention
            em.contributions.sort(key=lambda contr: contr[1], reverse=True)
            if len(em.contributions) > persona.scratch.retention:
                em.contributions = em.contributions[persona.scratch.retention:]
            ##print("EM CONTRS AFTER = " + str(em.name)+ " : " + str(em.contributions))

    def calculate_all_emotion_values(self, persona):

        self.trim_contribs(persona)

        for i in range(len(self.OCC.emotions)):
            self.OCC.emotions[i].value = self.calculate_emotion_value(self.OCC.emotions[i])
            #print("EM NOW " + str(self.OCC.emotions[i]))
             

    def calculate_emotion_value(self, emotion):
        value = 0
         
        if len(emotion.contributions)>0:
            for elem in emotion.contributions:
                V = float(elem[1])
                if emotion.name == "Anger" or emotion.name == "Gratification" or emotion.name =="Gratitude" or emotion.name =="Remorse":
                    value += (V)/2
                else:
                    value+= (V)
        
            return log_bounded_steep(value, K=10000, p=3.5)
    
        return value
    def re_appraise(self, appraisals, event, persona, personas, coping_strategy):
        t = time.time()


        existing_ongoing_appraisals = [appraisal.get("event") for appraisal in appraisals if appraisal.get("recency")=="ongoing"]
        existing_finished_appraisals = [appraisal.get("event") for appraisal in appraisals if appraisal.get("recency")=="finished"]
        
        if event in existing_ongoing_appraisals:
            appraisal = persona.emotional_layer.OCC.appraise(persona, event, "ongoing", personas,  coping_strategy=coping_strategy)

       
        elif event in existing_finished_appraisals:
            appraisal = persona.emotional_layer.OCC.appraise(persona, event, "finished", personas,  coping_strategy=coping_strategy)
        else:
            #print("NEEEEEEWWWWW ")

            appraisal = persona.emotional_layer.OCC.appraise(persona, event, "new", personas, coping_strategy=coping_strategy)
        
        
        
        index = None
        for i in range(len(appraisals)):
            if appraisals[i].get("event") == event:
                index = i
                break
        
        if index != None:
            appraisals[i] = appraisal
            


        #print("Re-APPRAISAL TOOK: " + str(time.time()-t) + " seconds to run")
        return appraisals
    

    def get_appraisals_from_llm(self, appraisals, event_triplet, persona, personas, chat=None):
        t = time.time()

        new_events, ongoing_events, finished_events = event_triplet

        existing_new_appraisals = [appraisal.get("event") for appraisal in appraisals if appraisal.get("recency")=="new"]
        existing_ongoing_appraisals = [appraisal.get("event") for appraisal in appraisals if appraisal.get("recency")=="ongoing"]
        existing_finished_appraisals = [appraisal.get("event") for appraisal in appraisals if appraisal.get("recency")=="finished"]

        #print("existing_finished_appraisals = ", str(existing_finished_appraisals))
        for p_event in new_events:
            #print(p_event)
            if p_event not in existing_new_appraisals:
                appraisal = persona.emotional_layer.OCC.appraise(persona, p_event, "new", personas)
                if persona.name == "Pepper Robot":
                    appraisal.update({"intensity": int(appraisal.get("intensity"))}) # recency multiplier
                else:
                    appraisal.update({"intensity": int(appraisal.get("intensity"))}) # recency multiplier
                appraisals.append(appraisal) 

        for p_event in ongoing_events:
            if p_event not in existing_ongoing_appraisals:
                appraisal = persona.emotional_layer.OCC.appraise(persona, p_event, "ongoing", personas)
                if persona.name == "Pepper Robot":
                    appraisal.update({"intensity": int(appraisal.get("intensity")*self.recency_multiplier_ongoing_events)}) # recency multiplier
                else:
                    appraisal.update({"intensity": int(appraisal.get("intensity")*self.recency_multiplier_ongoing_events)}) # recency multiplier

                appraisals.append(appraisal)

        for p_event in finished_events:
            if p_event not in existing_finished_appraisals:
                appraisal = persona.emotional_layer.OCC.appraise(persona, p_event, "finished", personas)
                if persona.name == "Pepper Robot":
                    appraisal.update({"intensity": int(appraisal.get("intensity")*self.recency_multiplier_finished_events)}) #recency multiplier
                else:
                    appraisal.update({"intensity": int(appraisal.get("intensity")*self.recency_multiplier_finished_events)}) #recency multiplier

                appraisals.append(appraisal)

        ap_ = "APPRAISAL TOOK: " + str(time.time()-t) + " seconds to run"
        ap = time.time()-t
        #print(ap_)
        em_ = self.find_predominant_emotions(1)[0]
        if chat is not None:
            chat[1].append(ap_)
            chat[2].append((datetime.datetime.now(), None, None, ap, f"{em_.name}:{em_.value}", None, None, None, None))

        return appraisals

    def print_layer(self, chat=None):
        self.OCC.emotions = self.find_predominant_emotions(len(self.OCC.emotions)) 
        strin = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}]\n"
        strin += "EMOTIONAL LAYER (" + self.name + ") Mood " + str(self.mood[0]) + " - BONUS " + str(self.mood[1]) + "\n"
        for elem in self.OCC.emotions:
            strin+=str(elem) + "\n"
        print(Fore.GREEN+ strin)
        print(Style.RESET_ALL)
        strin_2 = "DESCRIPTIONS: \n"
        for elem in self.OCC.emotions:
            if elem.value > 0:
                strin_2+= elem.get_description(self.name) + "\n"
        print(Fore.RED+ strin_2)
        print(Style.RESET_ALL)
        if chat:
            chat[1].append(strin + strin_2)


    def generate_appraisals(self, persona, personas, predominant_emotion = None, coping_strat=None):
        appraisals = []
        if predominant_emotion is not None:
            contrs = predominant_emotion.contributions
            contrs.sort(key=lambda contr: contr[1])
            contrs.reverse()
            event = contrs[0]
            print("RE APPRAISE")
            self.appraisals = self.re_appraise(self.appraisals, event[0], persona, personas, coping_strategy=coping_strat)

        else:
            self.appraisals = self.get_appraisals_from_llm(appraisals, self.event_triplet, persona, personas)
        curr_time = persona.scratch.curr_time
        #print("self.appraisals = " + str(self.appraisals))
        # checka se dá pra por retention nos eventos guardados por cada emoção - acho que está

        self.update(self.appraisals, persona.scratch.curr_time, persona)


        

    
    def get_event_triplet(self, events, current_triplet):
        new, ongoing, done = [],[],[]
        for event in events:
            new_events = [p_event for p_event in current_triplet[0] if (p_event[0],p_event[1], p_event[2])==(event[0], event[1], event[2])]
            ongoing_events = [p_event for p_event in current_triplet[1] if (p_event[0],p_event[1], p_event[2])==(event[0], event[1], event[2])]
            done_events = [p_event for p_event in current_triplet[2] if (p_event[0],p_event[1], p_event[2])==(event[0], event[1], event[2])]

            new+= new_events
            ongoing+=ongoing_events
            done+= done_events

        return new, ongoing, done
    
    def retrieve_intensity(self, event):
        p_event = event.subject, event.predicate, event.object
        ##print("EVENT = " + str(p_event) )

        for em in self.OCC.emotions:
            ##print(em.name)
            for contr in em.contributions:

                ##print("Contr = " + str(contr[0]))
                if p_event == (contr[0][0],contr[0][1],contr[0][2]):
                    ##print("HERE!")
                    return contr[1]
        return 0




