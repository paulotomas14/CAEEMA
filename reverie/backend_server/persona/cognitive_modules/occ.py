'''class EmotionalLayer:
    def __init__(self, )'''

from persona.prompt_template.gpt_structure import *
from persona.prompt_template.run_gpt_prompt import *



class Emotion:
    def __init__(self, coping, action_tendency, target_needed, description, name, category, valence, l_t, h_t, d):
        self.name = name
        self.category = category
        self.valence = valence
        self.low_threshold = l_t
        self.high_threshold = h_t
        self.decay = d
        self.contributions = []
        self.value = 0
        self.description = description
        self.target_needed = target_needed
        self.max_events_in_desc = 1
        self.coping_strategy = coping
        self.action_tendency = action_tendency
        
    def __str__(self):
        return str((self.name, self.value, str(self.contributions)))
    
    def __repr__(self):
        return str((self.name, self.value, str(self.contributions)))
    
    def get_main_contribution(self):
        contrs = self.contributions
        contrs.sort(key=lambda contr: contr[1])
        contrs.reverse()
        if len(contrs)>0:
            return contrs[0]
        return None
    
    def get_description(self, name):
        desc = ""
        contrs = self.contributions
        contrs.sort(key=lambda contr: contr[1])
        contrs.reverse()

        max_ev = min(self.max_events_in_desc, len(contrs))
        for i in range(max_ev):
            ##print("CONTR to " + str(name)+ "'s " + str(self.name) + ": " + str(contrs[i]))
            event_description = " the event: [" + str(contrs[i][0][3]) + "] "
            reason = contrs[i][2]
            if self.target_needed:
                target = contrs[i][3]
                desc+= name +self.description.format(target, event_description, reason) + "\n"
            else:
                desc+= name +self.description.format(event_description, reason) + "\n"
        ##print(desc)             
        return desc

class OCCModel:
    def __init__(self, map, emotional_layer):
        self.emotions = self.initialize_emotions(map, emotional_layer)
        self.restore_emotional_layer(emotional_layer)


    def initialize_emotions(self, map, emotional_layer):
        emotions = []
        # Event-based emotions
        ##print(map)
        emotions.append(Emotion(map["Joy"]["coping"], map["Joy"]["action_tendency"], map["Joy"]["target_needed"], map["Joy"]["description"],"Joy", "Event-based", "Positive", map["Joy"]["l_t"], map["Joy"]["h_t"], map["Joy"]["decay"]))
        emotions.append(Emotion(map["Distress"]["coping"], map["Distress"]["action_tendency"], map["Distress"]["target_needed"], map["Distress"]["description"],"Distress", "Event-based", "Negative", map["Distress"]["l_t"], map["Distress"]["h_t"], map["Distress"]["decay"]))
        emotions.append(Emotion(map["Happy-for"]["coping"], map["Happy-for"]["action_tendency"], map["Happy-for"]["target_needed"], map["Happy-for"]["description"],"Happy-for", "Event-based", "Positive", map["Happy-for"]["l_t"], map["Happy-for"]["h_t"], map["Happy-for"]["decay"]))
        emotions.append(Emotion(map["Gloating"]["coping"], map["Gloating"]["action_tendency"], map["Gloating"]["target_needed"], map["Gloating"]["description"],"Gloating", "Event-based", "Positive", map["Gloating"]["l_t"], map["Gloating"]["h_t"], map["Gloating"]["decay"]))
        emotions.append(Emotion(map["Resentment"]["coping"], map["Resentment"]["action_tendency"], map["Resentment"]["target_needed"], map["Resentment"]["description"],"Resentment", "Event-based", "Negative", map["Resentment"]["l_t"], map["Resentment"]["h_t"], map["Resentment"]["decay"]))
        emotions.append(Emotion(map["Sorry-for"]["coping"], map["Sorry-for"]["action_tendency"], map["Sorry-for"]["target_needed"], map["Sorry-for"]["description"],"Sorry-for", "Event-based", "Negative", map["Sorry-for"]["l_t"], map["Sorry-for"]["h_t"], map["Sorry-for"]["decay"]))
        emotions.append(Emotion(map["Hope"]["coping"], map["Hope"]["action_tendency"], map["Hope"]["target_needed"], map["Hope"]["description"],"Hope", "Event-based", "Positive", map["Hope"]["l_t"], map["Hope"]["h_t"], map["Hope"]["decay"]))
        emotions.append(Emotion(map["Fear"]["coping"], map["Fear"]["action_tendency"], map["Fear"]["target_needed"], map["Fear"]["description"],"Fear", "Event-based", "Negative", map["Fear"]["l_t"], map["Fear"]["h_t"], map["Fear"]["decay"]))
        emotions.append(Emotion(map["Relief"]["coping"], map["Relief"]["action_tendency"], map["Relief"]["target_needed"], map["Relief"]["description"],"Relief", "Event-based", "Positive", map["Relief"]["l_t"], map["Relief"]["h_t"], map["Relief"]["decay"]))
        emotions.append(Emotion(map["Disappointment"]["coping"], map["Disappointment"]["action_tendency"], map["Disappointment"]["target_needed"], map["Disappointment"]["description"],"Disappointment", "Event-based", "Negative", map["Disappointment"]["l_t"], map["Disappointment"]["h_t"], map["Disappointment"]["decay"]))
        emotions.append(Emotion(map["Satisfaction"]["coping"], map["Satisfaction"]["action_tendency"], map["Satisfaction"]["target_needed"], map["Satisfaction"]["description"],"Satisfaction", "Event-based", "Positive", map["Satisfaction"]["l_t"], map["Satisfaction"]["h_t"], map["Satisfaction"]["decay"]))
        emotions.append(Emotion(map["Fears-confirmed"]["coping"], map["Fears-confirmed"]["action_tendency"], map["Fears-confirmed"]["target_needed"], map["Fears-confirmed"]["description"],"Fears-confirmed", "Event-based", "Negative", map["Fears-confirmed"]["l_t"], map["Fears-confirmed"]["h_t"], map["Fears-confirmed"]["decay"]))

        #attribution-based
        emotions.append(Emotion(map["Pride"]["coping"], map["Pride"]["action_tendency"], map["Pride"]["target_needed"], map["Pride"]["description"], "Pride", "Attribution-based", "Positive", map["Pride"]["l_t"], map["Pride"]["h_t"], map["Pride"]["decay"]))
        emotions.append(Emotion(map["Shame"]["coping"], map["Shame"]["action_tendency"], map["Shame"]["target_needed"], map["Shame"]["description"], "Shame", "Attribution-based", "Negative", map["Shame"]["l_t"], map["Shame"]["h_t"], map["Shame"]["decay"]))
        emotions.append(Emotion(map["Admiration"]["coping"], map["Admiration"]["action_tendency"], map["Admiration"]["target_needed"], map["Admiration"]["description"], "Admiration", "Attribution-based", "Positive", map["Admiration"]["l_t"], map["Admiration"]["h_t"], map["Admiration"]["decay"]))
        emotions.append(Emotion(map["Reproach"]["coping"], map["Reproach"]["action_tendency"], map["Reproach"]["target_needed"], map["Reproach"]["description"], "Reproach", "Attribution-based", "Negative", map["Reproach"]["l_t"], map["Reproach"]["h_t"], map["Reproach"]["decay"]))

        # Object-based emotions
        emotions.append(Emotion(map["Love"]["coping"], map["Love"]["action_tendency"], map["Love"]["target_needed"], map["Love"]["description"], "Love", "Object-based", "Positive", map["Love"]["l_t"], map["Love"]["h_t"], map["Love"]["decay"]))
        emotions.append(Emotion(map["Hate"]["coping"], map["Hate"]["action_tendency"], map["Hate"]["target_needed"], map["Hate"]["description"], "Hate", "Object-based", "Negative", map["Hate"]["l_t"], map["Hate"]["h_t"], map["Hate"]["decay"]))

        #add compounds?
        emotions.append(Emotion(map["Gratification"]["coping"], map["Gratification"]["action_tendency"], map["Gratification"]["target_needed"], map["Gratification"]["description"], "Gratification", "Compound", "Positive", map["Gratification"]["l_t"], map["Gratification"]["h_t"], map["Gratification"]["decay"]))
        emotions.append(Emotion(map["Remorse"]["coping"], map["Remorse"]["action_tendency"], map["Remorse"]["target_needed"], map["Remorse"]["description"], "Remorse", "Compound", "Negative", map["Remorse"]["l_t"], map["Remorse"]["h_t"], map["Remorse"]["decay"]))
        emotions.append(Emotion(map["Gratitude"]["coping"], map["Gratitude"]["action_tendency"], map["Gratitude"]["target_needed"], map["Gratitude"]["description"], "Gratitude", "Compound", "Positive", map["Gratitude"]["l_t"], map["Gratitude"]["h_t"], map["Gratitude"]["decay"]))
        emotions.append(Emotion(map["Anger"]["coping"], map["Anger"]["action_tendency"], map["Anger"]["target_needed"], map["Anger"]["description"], "Anger", "Compound", "Negative", map["Anger"]["l_t"], map["Anger"]["h_t"], map["Anger"]["decay"]))

        return emotions
    
    def restore_emotional_layer(self, emotional_layer):
        for key in emotional_layer.keys():
            em = emotional_layer.get(key)
            value = 0
            memories = []

            for contribution in em:
                value+= contribution[1]
                memories.append(contribution)

            emotion = self.find_emotion(key)
            emotion.contributions = memories
            emotion.value = value

    def trigger_event_based_emotion(self, affected_party, prospect, appeal, dislike, confirmed): 
        if  "self" == affected_party.strip().lower():
            if prospect:
                if appeal:
                    if confirmed == True:
                        return self.find_emotion("Satisfaction")
                    elif confirmed == False:
                        return self.find_emotion("Relief")
                    else:
                        return self.find_emotion("Hope")
                else:
                    if confirmed == True:
                        return self.find_emotion("Fears-confirmed")
                    elif confirmed == False:
                        return self.find_emotion("Disappointment")
                    else:
                        return self.find_emotion("Fear")
                    
            else:
                if appeal:
                    return self.find_emotion("Joy")
                else:
                    return self.find_emotion("Distress")
        else:
            if appeal:
                if dislike:
                    return self.find_emotion("Resentment")
                else:
                    return self.find_emotion("Happy-for")
            else:
                if dislike:
                    return self.find_emotion("Gloating")
                else:
                    return self.find_emotion("Pity")
                
        return self.find_emotion("Joy")


                         


        
            
    def trigger_attribution_based_emotion(self, action_outcome, actor):
        ##print(f'ACTION OUTCOME = {action_outcome}')
        if action_outcome == True:
            if actor == "self":
                return self.find_emotion("Pride")
            else:
                return self.find_emotion("Admiration")
        else:
            if actor == "self":
                return self.find_emotion("Shame")
            else:
                return self.find_emotion("Reproach")
            
        return self.find_emotion("Pride")

    def trigger_object_based_emotion(self, object_value):
        return self.find_emotion("Love") if object_value == True else self.find_emotion("Hate")

    def find_emotion(self, emotion_name):
        for emotion in self.emotions:
            if emotion.name == emotion_name:
                return emotion
        ##print("EMOTION = " + emotion_name)
        return "No Emotion"
    
    def get_appraisal(self,recency, event, reason, emotion, intensity, affected_party):
        ##print(event, reason, emotion, intensity)
        return {"recency": recency, "event":event, "reason": reason, "emotion" : emotion.name, "category" : emotion.category, "valence" : emotion.valence, "intensity":intensity, "target": affected_party}


    def display_emotion(self, emotion):
        if emotion:
            print(f"Emotion: {emotion.name}, Category: {emotion.category}, Valence: {emotion.valence}")
        else:
            print("No emotion triggered.")

    def get_emotion(self, agent, event, personas, finished, coping_strategy = None):
        personas_str = [p.lower() for p in personas.keys()]
        #print(event)
        #print(coping_strategy)
        subject, predicate, obj, desc = event         

        if agent.name.lower() in subject.strip().lower():
            actor = "self"
        elif subject.strip().lower() in personas_str:
            actor = "other"
        else:
            actor = "none"

        #print(f'SUBJECT = {subject}, AGENT = {agent.name}, actor = {actor}, object = {obj}')

        if actor == "self" or actor == "other":
            affected_party = subject
            reason, appeal, intensity = get_gpt_appraisal_attribute_based(agent, event, coping_strategy=coping_strategy)[0]
            appraisal = reason, self.trigger_attribution_based_emotion(appeal, actor), intensity, affected_party
        elif actor == "none" and obj != "idle":
            
            reason, affected_party, prospect, appeal, dislike, confirmed, intensity  = get_gpt_appraisal_event_based(agent, event, finished, coping_strategy=coping_strategy)[0]
            if finished != "finished":
                confirmed = None
            appraisal = reason, self.trigger_event_based_emotion(affected_party, prospect, appeal, dislike, confirmed), intensity, affected_party
        else:
            affected_party = subject
            #print("NO COMPRENDO!")
            reason, appeal, intensity = get_gpt_appraisal_object_based(agent, event, coping_strategy=coping_strategy)[0]
            appraisal = reason, self.trigger_object_based_emotion(appeal), intensity, affected_party
        #print(appraisal)
        try:
            emotion_name = appraisal[1].name
        except AttributeError:
            emotion = self.emotions[0]
            appraisal = appraisal[0], emotion, 0, appraisal[3]
        return appraisal
        
    def appraise(self, agent, event, finished, personas, coping_strategy=None, queue=None):
        reason, emotion, intensity, affected_party = self.get_emotion(agent, event, personas, finished, coping_strategy=coping_strategy)
        app = self.get_appraisal(finished, event, reason, emotion, intensity , affected_party)
        if queue is not None:
            queue.put(app)
        else:
            return app


        