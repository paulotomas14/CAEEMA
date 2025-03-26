"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: persona.py
Description: Defines the Persona class that powers the agents in Reverie. 

Note (May 1, 2023) -- this is effectively GenerativeAgent class. Persona was
the term we used internally back in 2022, taking from our Social Simulacra 
paper.
"""
import math
import sys
import datetime
import random
sys.path.append('../')

from global_methods import *

from persona.memory_structures.spatial_memory import *
from persona.memory_structures.associative_memory import *
from persona.memory_structures.scratch import *
from persona.memory_structures.calendar import *

from persona.cognitive_modules.perceive import *
from persona.cognitive_modules.retrieve import *
from persona.cognitive_modules.plan import *
from persona.cognitive_modules.reflect import *
from persona.cognitive_modules.execute import *
from persona.cognitive_modules.converse import *
from persona.cognitive_modules.emotional_layer import *

class Persona: 
  def __init__(self, name, curr_time, folder_mem_saved=False, emotional=False, new=False):
    # PERSONA BASE STATE 
    # <name> is the full name of the persona. This is a unique identifier for
    # the persona within Reverie. 
    self.name = name

    # PERSONA MEMORY 
    # If there is already memory in folder_mem_saved, we load that. Otherwise,
    # we create new memory instances. 
    # <s_mem> is the persona's spatial memory. 
    f_s_mem_saved = f"{folder_mem_saved}/bootstrap_memory/spatial_memory.json"
    self.s_mem = MemoryTree(f_s_mem_saved)
    # <s_mem> is the persona's associative memory. 
    f_a_mem_saved = f"{folder_mem_saved}/bootstrap_memory/associative_memory"
    self.a_mem = AssociativeMemory(f_a_mem_saved, new)
    # <scratch> is the persona's scratch (short term memory) space. 
    scratch_saved = f"{folder_mem_saved}/bootstrap_memory/scratch.json"
    self.scratch = Scratch(scratch_saved, curr_time=curr_time)

    calendar_saved = f"{folder_mem_saved}/bootstrap_memory/calendar.json"
    self.calendar = Calendar(calendar_saved, new)
    self.scratch.calendar = self.calendar
    #self.current_convo = []
    self.refresh_summary = 5
    self.counter_summary_refresh = -1
    self.convo_summary = ""
    self.emotional = emotional
    if self.emotional:
      emotional_map = f"{folder_mem_saved}/characteristics/emotional_map.json"
      emotional_state = f"{folder_mem_saved}/bootstrap_memory/emotional_layer.json"
      self.emotional_layer = EmotionalLayer(name, emotional_map, emotional_state, self.scratch.curr_time)
      self.emotional_layer.update([], self.scratch.curr_time, self)
    else:
      self.emotional_layer = None


  def save(self, save_folder): 
    """
    Save persona's current state (i.e., memory). 

    INPUT: 
      save_folder: The folder where we wil be saving our persona's state. 
    OUTPUT: 
      None
    """
    # Spatial memory contains a tree in a json format. 
    # e.g., {"double studio": 
    #         {"double studio": 
    #           {"bedroom 2": 
    #             ["painting", "easel", "closet", "bed"]}}}
    #print("SAVING =" + str(self.name))
    f_s_mem = f"{save_folder}/spatial_memory.json"
    self.s_mem.save(f_s_mem)
    
    # Associative memory contains a csv with the following rows: 
    # [event.type, event.created, event.expiration, s, p, o]
    # e.g., event,2022-10-23 00:00:00,,Isabella Rodriguez,is,idle
    f_a_mem = f"{save_folder}/associative_memory"
    self.a_mem.save(f_a_mem)

    # Scratch contains non-permanent data associated with the persona. When 
    # it is saved, it takes a json form. When we load it, we move the values
    # to Python variables. 
    f_scratch = f"{save_folder}/scratch.json"
    self.scratch.save(f_scratch)

    f_calendar = f"{save_folder}/calendar.json"
    self.calendar.save(f_calendar, self.scratch.curr_time)

    if self.emotional:
      #print("SAVING EMO")
      folder_emo = f"{save_folder}/emotional_layer.json"
      self.emotional_layer.save(folder_emo)


  def perceive(self, maze, personas):
    """
    This function takes the current maze, and returns events that are 
    happening around the persona. Importantly, perceive is guided by 
    two key hyper-parameter for the  persona: 1) att_bandwidth, and 
    2) retention. 

    First, <att_bandwidth> determines the number of nearby events that the 
    persona can perceive. Say there are 10 events that are within the vision
    radius for the persona -- perceiving all 10 might be too much. So, the 
    persona perceives the closest att_bandwidth number of events in case there
    are too many events. 

    Second, the persona does not want to perceive and think about the same 
    event at each time step. That's where <retention> comes in -- there is 
    temporal order to what the persona remembers. So if the persona's memory
    contains the current surrounding events that happened within the most 
    recent retention, there is no need to perceive that again. xx

    INPUT: 
      maze: Current <Maze> instance of the world. 
    OUTPUT: 
      a list of <ConceptNode> that are perceived and new. 
        See associative_memory.py -- but to get you a sense of what it 
        receives as its input: "s, p, o, desc, persona.scratch.curr_time"
    """
    return perceive(self, maze, personas)


  def retrieve(self, perceived):
    """
    This function takes the events that are perceived by the persona as input
    and returns a set of related events and thoughts that the persona would 
    need to consider as context when planning. 

    INPUT: 
      perceive: a list of <ConceptNode> that are perceived and new.  
    OUTPUT: 
      retrieved: dictionary of dictionary. The first layer specifies an event,
                 while the latter layer specifies the "curr_event", "events", 
                 and "thoughts" that are relevant.
    """
    return retrieve(self, perceived)


  def plan(self, maze, personas, new_day, retrieved, event_triplet):
    """
    Main cognitive function of the chain. It takes the retrieved memory and 
    perception, as well as the maze and the first day state to conduct both 
    the long term and short term planning for the persona. 

    INPUT: 
      maze: Current <Maze> instance of the world. 
      personas: A dictionary that contains all persona names as keys, and the 
                Persona instance as values. 
      new_day: This can take one of the three values. 
        1) <Boolean> False -- It is not a "new day" cycle (if it is, we would
           need to call the long term planning sequence for the persona). 
        2) <String> "First day" -- It is literally the start of a simulation,
           so not only is it a new day, but also it is the first day. 
        2) <String> "New day" -- It is a new day. 
      retrieved: dictionary of dictionary. The first layer specifies an event,
                 while the latter layer specifies the "curr_event", "events", 
                 and "thoughts" that are relevant.
    OUTPUT 
      The target action address of the persona (persona.scratch.act_address).
    """
    return plan(self, maze, personas, new_day, retrieved, event_triplet)


  def execute(self, maze, personas, plan):
    """
    This function takes the agent's current plan and outputs a concrete 
    execution (what object to use, and what tile to travel to). 

    INPUT: 
      maze: Current <Maze> instance of the world. 
      personas: A dictionary that contains all persona names as keys, and the 
                Persona instance as values. 
      plan: The target action address of the persona  
            (persona.scratch.act_address).
    OUTPUT: 
      execution: A triple set that contains the following components: 
        <next_tile> is a x,y coordinate. e.g., (58, 9)
        <pronunciatio> is an emoji.
        <description> is a string description of the movement. e.g., 
        writing her next novel (editing her novel) 
        @ double studio:double studio:common room:sofa
    """
    return execute(self, maze, personas, plan)


  def reflect(self):
    """
    Reviews the persona's memory and create new thoughts based on it. 

    INPUT: 
      None
    OUTPUT: 
      None
    """
    reflect(self)


  def move(self, maze, personas, curr_tile, curr_time):
    """
    This is the main cognitive function where our main sequence is called. 

    INPUT: 
      maze: The Maze class of the current world. 
      personas: A dictionary that contains all persona names as keys, and the 
                Persona instance as values. 
      curr_tile: A tuple that designates the persona's current tile location 
                 in (row, col) form. e.g., (58, 39)
      curr_time: datetime instance that indicates the game's current time. 
    OUTPUT: 
      execution: A triple set that contains the following components: 
        <next_tile> is a x,y coordinate. e.g., (58, 9)
        <pronunciatio> is an emoji.
        <description> is a string description of the movement. e.g., 
        writing her next novel (editing her novel) 
        @ double studio:double studio:common room:sofa
    """
    # Updating persona's scratch memory with <curr_tile>. 
    self.scratch.curr_tile = curr_tile

    # We figure out whether the persona started a new day, and if it is a new
    # day, whether it is the very first day of the simulation. This is 
    # important because we set up the persona's long term plan at the start of
    # a new day. 
    new_day = False
    if not self.scratch.curr_time: 
      new_day = "First day"
    elif (self.scratch.curr_time.strftime('%A %B %d')
          != curr_time.strftime('%A %B %d')):
      new_day = "New day"
    self.scratch.curr_time = curr_time
    time_0 = time.time()
    # Main cognitive sequence begins here. 
    perceived, new, ongoing, finished = self.perceive(maze, personas)
    time_1 = time.time()
    print("Perceive = " + str(time_1-time_0))
    
    if self.emotional:
      event_triplet = (new, ongoing,finished)
      self.emotional_layer.event_triplet = event_triplet
    else:
      event_triplet = None
    
    retrieved = self.retrieve(perceived)
    time_3 = time.time()
    print("Retrieve = " + str(time_3-time_1))
    ##print("RETRIEVE DONE")
    plan = self.plan(maze, personas, new_day, retrieved, event_triplet)
    time_4 = time.time()
    print("Plan = " + str(time_4-time_3))
    self.reflect()
    time_5 = time.time()
    print("Reflect = " + str(time_5-time_4))


    # <execution> is a triple set that contains the following components: 
    # <next_tile> is a x,y coordinate. e.g., (58, 9)
    # <pronunciatio> is an emoji. e.g., "\ud83d\udca4"
    # <description> is a string description of the movement. e.g., 
    #   writing her next novel (editing her novel) 
    #   @ double studio:double studio:common room:sofa
    return self.execute(maze, personas, plan)


  def open_convo_session(self, convo_mode, personas=None, chat_partner=None, line=None, curr_convo=None, curr_summmary=None,curr_time=None, out_q=None, relationship=None, new_env=None, par= None, memories=None ): 
    return open_convo_session(self, convo_mode, personas, chat_partner, line, curr_convo, curr_summmary, curr_time, out_q, relationship, new_env, par, memories)
    

  def main_robot_convo_loop(self, new_env, human, personas,curr_time,begin):
    
    self.scratch.curr_time = curr_time

    # Main cognitive sequence begins here. 
    ##print("perceive")
    perceived = self.perceive_robot(new_env, personas, human)
    ##print("retirve")
    ##print("PERCEIVED = " + str(perceived))
    retrieved = self.retrieve(perceived)
    ##print(retrieved)
    new_day = False
    if begin:
      new_day = "First day"
    else:
      if curr_time.hour == 0:
        new_day = "New day"


    '''#print("RETRIEVED= ")
    for r in retrieved:
      #print(Fore.GREEN + str(r))
    #print(Style.RESET_ALL)'''
    ##print("Plan")
    plan = self.plan_robot(personas, new_day, retrieved, human)
    ##print("reflect")
    self.reflect()
    ##print("Execute")


    return self.execute_robot( personas, plan)
  
  def setup_convo_robot(self, line, human):
    """
    Perceives events around the persona and saves it to the memory, both events 
    and spaces. 

    We first perceive the events nearby the persona, as determined by its 
    <vision_r>. If there are a lot of events happening within that radius, we 
    take the <att_bandwidth> of the closest events. Finally, we check whether
    any of them are new, as determined by <retention>. If they are new, then we
    save those and return the <ConceptNode> instances for those events. 

    INPUT: 
      persona: An instance of <Persona> that represents the current persona. 
      maze: An instance of <Maze> that represents the current maze in which the 
            persona is acting in. 
    OUTPUT: 
      ret_events: a list of <ConceptNode> that are perceived and new. 
    """

    percept_events_list = []
    perceived_events = []

    s = human
    o = self.name
    p = "chat with"
    desc = line

    percept_events_list.append((s,p,o,desc))
    

    for event in percept_events_list[:self.scratch.att_bandwidth]: 
      perceived_events += [event]

    # Storing events. 
    # <ret_events> is a list of <ConceptNode> instances from the persona's 
    # associative memory. 
    ret_events = []
    for p_event in perceived_events: 
      s, p, o, desc = p_event
      if not p: 
        # If the object is not present, then we default the event to "idle".
        p = "is"
        o = "idle"
        desc = "idle"

      p_event = (s, p, o)

      # We retrieve the latest persona.scratch.retention events. If there is  
      # something new that is happening (that is, p_event not in latest_events),
      # then we add that event to the a_mem and return it. 
    
      # We start by managing keywords. 
      keywords = set()
      sub = p_event[0]
      obj = p_event[2]
      if ":" in p_event[0]: 
        sub = p_event[0].split(":")[-1]
      if ":" in p_event[2]: 
        obj = p_event[2].split(":")[-1]
      keywords.update([sub, obj])
      ##print("EMB POIG 1")

      # Get event embedding
      desc_embedding_in = desc
      if "(" in desc: 
        desc_embedding_in = (desc_embedding_in.split("(")[1]
                                              .split(")")[0]
                                              .strip())
      if desc_embedding_in in self.a_mem.embeddings: 
        event_embedding = self.a_mem.embeddings[desc_embedding_in]
      else:
        event_embedding = get_embedding(desc_embedding_in)
      event_embedding_pair = (desc_embedding_in, event_embedding)
      
      # Get event poignancy. 
      event_poignancy = generate_poig_score(self, 
                                            "event", 
                                            desc_embedding_in)

      # If we observe the persona's self chat, we include that in the memory
      # of the persona here. 
      chat_node_ids = []
     

      curr_event = self.scratch.act_event
      if self.scratch.act_description in self.a_mem.embeddings: 
        chat_embedding = self.a_mem.embeddings[
                          self.scratch.act_description]
      else: 
        chat_embedding = get_embedding(self.scratch
                                              .act_description)
      chat_embedding_pair = (self.scratch.act_description, 
                            chat_embedding)
      chat_poignancy = generate_poig_score(self, "chat", 
                                          self.scratch.act_description)
      chat_node = self.a_mem.add_chat(self.scratch.curr_time, None,
                    curr_event[0], curr_event[1], curr_event[2], 
                    self.scratch.act_description, keywords, 
                    chat_poignancy, chat_embedding_pair, 
                    self.scratch.chat)
      chat_node_ids = [chat_node.node_id]

    # Finally, we add the current event to the agent's memory. 
    ret_events += [self.a_mem.add_event(self.scratch.curr_time, None,
                        s, p, o, desc, keywords, event_poignancy, 
                        event_embedding_pair, chat_node_ids)]
    self.scratch.importance_trigger_curr -= event_poignancy
    self.scratch.importance_ele_n += 1    

    return ret_events
  

  def execute_robot(self, personas, plan):
    description = f"{self.scratch.act_description}"
    description += f" @ {self.scratch.act_address}"
    execution =  self.scratch.act_pronunciatio, description
    for i in range(len(self.scratch.chat)-1,0, -1):
      if self.scratch.chat[i][0] == self.name:
        print(Fore.RED + str(self.name))
        print(Fore.CYAN + str(self.scratch.chat[i][1]))
        print(Style.RESET_ALL)
        #break in the future
      else:
        print(i)
    return execution




































