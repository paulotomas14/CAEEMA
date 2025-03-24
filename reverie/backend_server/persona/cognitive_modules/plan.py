"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: plan.py
Description: This defines the "Plan" module for generative agents. 
"""
import datetime
import math
import random 
import sys
import time
sys.path.append('../../')

from global_methods import *
from persona.prompt_template.run_gpt_prompt import *
from persona.cognitive_modules.retrieve import *
from persona.cognitive_modules.converse import *
from utils import *

##############################################################################
# CHAPTER 2: Generate
##############################################################################

def generate_wake_up_hour(persona):
  """
  Generates the time when the persona wakes up. This becomes an integral part
  of our process for generating the persona's daily plan.
  
  Persona state: identity stable set, lifestyle, first_name

  INPUT: 
    persona: The Persona class instance 
  OUTPUT: 
    an integer signifying the persona's wake up hour
  EXAMPLE OUTPUT: 
    8
  """
  #if debug: 
  #print ("GNS FUNCTION: <generate_wake_up_hour>")
  hour = int(run_gpt_prompt_wake_up_hour(persona)[0])
  #print("WAKE UP HOUR = " + str(hour))
  return hour


def generate_first_daily_plan(persona, wake_up_hour): 
  """
  Generates the daily plan for the persona. 
  Basically the long term planning that spans a day. Returns a list of actions
  that the persona will take today. Usually comes in the following form: 
  'wake up and complete the morning routine at 6:00 am', 
  'eat breakfast at 7:00 am',.. 
  Note that the actions come without a period. 

  Persona state: identity stable set, lifestyle, cur_data_str, first_name

  INPUT: 
    persona: The Persona class instance 
    wake_up_hour: an integer that indicates when the hour the persona wakes up 
                  (e.g., 8)
  OUTPUT: 
    a list of daily actions in broad strokes.
  EXAMPLE OUTPUT: 
    ['wake up and complete the morning routine at 6:00 am', 
     'have breakfast and brush teeth at 6:30 am',
     'work on painting project from 8:00 am to 12:00 pm', 
     'have lunch at 12:00 pm', 
     'take a break and watch TV from 2:00 pm to 4:00 pm', 
     'work on painting project from 4:00 pm to 6:00 pm', 
     'have dinner at 6:00 pm', 'watch TV from 7:00 pm to 8:00 pm']
  """
  if debug: print ("GNS FUNCTION: <generate_first_daily_plan>")
  return run_gpt_prompt_daily_plan(persona, wake_up_hour)[0]



def generate_hourly_schedule(persona, wake_up_hour): 
  """
  Based on the daily req, creates an hourly schedule -- one hour at a time. 
  The form of the action for each of the hour is something like below: 
  "sleeping in her bed"
  
  The output is basically meant to finish the phrase, "x is..."

  Persona state: identity stable set, daily_plan

  INPUT: 
    persona: The Persona class instance 
    persona: Integer form of the wake up hour for the persona.  
  OUTPUT: 
    a list of activities and their duration in minutes: 
  EXAMPLE OUTPUT: 
    [['sleeping', 360], ['waking up and starting her morning routine', 60], 
     ['eating breakfast', 60],..
  """
  if debug: print ("GNS FUNCTION: <generate_hourly_schedule>")

  hour_str = ["00:00 AM", "01:00 AM", "02:00 AM", "03:00 AM", "04:00 AM", 
              "05:00 AM", "06:00 AM", "07:00 AM", "08:00 AM", "09:00 AM", 
              "10:00 AM", "11:00 AM", "12:00 PM", "01:00 PM", "02:00 PM", 
              "03:00 PM", "04:00 PM", "05:00 PM", "06:00 PM", "07:00 PM",
              "08:00 PM", "09:00 PM", "10:00 PM", "11:00 PM"]
  n_m1_activity = []
  diversity_repeat_count = 3
  for i in range(diversity_repeat_count): 
    n_m1_activity_set = set(n_m1_activity)
    if len(n_m1_activity_set) < 5: 
      n_m1_activity = []
      for count, curr_hour_str in enumerate(hour_str): 
        if wake_up_hour > 0: 
          n_m1_activity += ["sleeping"]
          wake_up_hour -= 1
        else: 
          n_m1_activity += [run_gpt_prompt_generate_hourly_schedule(
                          persona, curr_hour_str, n_m1_activity, hour_str)[0]]
  
  # Step 1. Compressing the hourly schedule to the following format: 
  # The integer indicates the number of hours. They should add up to 24. 
  # [['sleeping', 6], ['waking up and starting her morning routine', 1], 
  # ['eating breakfast', 1], ['getting ready for the day', 1], 
  # ['working on her painting', 2], ['taking a break', 1], 
  # ['having lunch', 1], ['working on her painting', 3], 
  # ['taking a break', 2], ['working on her painting', 2], 
  # ['relaxing and watching TV', 1], ['going to bed', 1], ['sleeping', 2]]
  _n_m1_hourly_compressed = []
  prev = None 
  prev_count = 0
  for i in n_m1_activity: 
    if i != prev:
      prev_count = 1 
      _n_m1_hourly_compressed += [[i, prev_count]]
      prev = i
    else: 
      if _n_m1_hourly_compressed: 
        _n_m1_hourly_compressed[-1][1] += 1

  # Step 2. Expand to min scale (from hour scale)
  # [['sleeping', 360], ['waking up and starting her morning routine', 60], 
  # ['eating breakfast', 60],..
  n_m1_hourly_compressed = []
  for task, duration in _n_m1_hourly_compressed: 
    n_m1_hourly_compressed += [[task, duration*60]]

  return n_m1_hourly_compressed


def coping_re_generate_hourly_schedule(persona): 
  """
  Based on the daily req, creates an hourly schedule -- one hour at a time. 
  The form of the action for each of the hour is something like below: 
  "sleeping in her bed"
  
  The output is basically meant to finish the phrase, "x is..."

  Persona state: identity stable set, daily_plan

  INPUT: 
    persona: The Persona class instance 
    persona: Integer form of the wake up hour for the persona.  
  OUTPUT: 
    a list of activities and their duration in minutes: 
  EXAMPLE OUTPUT: 
    [['sleeping', 360], ['waking up and starting her morning routine', 60], 
     ['eating breakfast', 60],..
  """
  if debug: print ("GNS FUNCTION: <generate_hourly_schedule>")

  hour_str = ["00:00 AM", "01:00 AM", "02:00 AM", "03:00 AM", "04:00 AM", 
              "05:00 AM", "06:00 AM", "07:00 AM", "08:00 AM", "09:00 AM", 
              "10:00 AM", "11:00 AM", "12:00 PM", "01:00 PM", "02:00 PM", 
              "03:00 PM", "04:00 PM", "05:00 PM", "06:00 PM", "07:00 PM",
              "08:00 PM", "09:00 PM", "10:00 PM", "11:00 PM"]
  n_m1_activity = []
  diversity_repeat_count = 3
  for i in range(diversity_repeat_count): 
    n_m1_activity_set = set(n_m1_activity)
    start = False
    if len(n_m1_activity_set) < 5: 
      n_m1_activity = []
      for count, curr_hour_str in enumerate(hour_str): 
        curr_hour = persona.scratch.curr_time.replace(minute=0, second=0) 
        if curr_hour_str == curr_hour.strftime("%I:%M %p"):
          start = True
        if start:
          n_m1_activity += [run_gpt_prompt_generate_hourly_schedule(
                          persona, curr_hour_str, n_m1_activity, hour_str)[0]]
  
  # Step 1. Compressing the hourly schedule to the following format: 
  # The integer indicates the number of hours. They should add up to 24. 
  # [['sleeping', 6], ['waking up and starting her morning routine', 1], 
  # ['eating breakfast', 1], ['getting ready for the day', 1], 
  # ['working on her painting', 2], ['taking a break', 1], 
  # ['having lunch', 1], ['working on her painting', 3], 
  # ['taking a break', 2], ['working on her painting', 2], 
  # ['relaxing and watching TV', 1], ['going to bed', 1], ['sleeping', 2]]
  _n_m1_hourly_compressed = []
  prev = None 
  prev_count = 0
  for i in n_m1_activity: 
    if i != prev:
      prev_count = 1 
      _n_m1_hourly_compressed += [[i, prev_count]]
      prev = i
    else: 
      if _n_m1_hourly_compressed: 
        _n_m1_hourly_compressed[-1][1] += 1

  # Step 2. Expand to min scale (from hour scale)
  # [['sleeping', 360], ['waking up and starting her morning routine', 60], 
  # ['eating breakfast', 60],..
  n_m1_hourly_compressed = []
  for task, duration in _n_m1_hourly_compressed: 
    n_m1_hourly_compressed += [[task, duration*60]]

  return n_m1_hourly_compressed


def generate_task_decomp(persona, task, duration): 
  """
  A few shot decomposition of a task given the task description 

  Persona state: identity stable set, curr_date_str, first_name

  INPUT: 
    persona: The Persona class instance 
    task: the description of the task at hand in str form
          (e.g., "waking up and starting her morning routine")
    duration: an integer that indicates the number of minutes this task is 
              meant to last (e.g., 60)
  OUTPUT: 
    a list of list where the inner list contains the decomposed task 
    description and the number of minutes the task is supposed to last. 
  EXAMPLE OUTPUT: 
    [['going to the bathroom', 5], ['getting dressed', 5], 
     ['eating breakfast', 15], ['checking her email', 5], 
     ['getting her supplies ready for the day', 15], 
     ['starting to work on her painting', 15]] 

  """
  #if debug: 
  #print ("GNS FUNCTION: <generate_task_decomp>")
  out = run_gpt_prompt_task_decomp(persona, task, duration)[0]
  #print("DONE GNS BSUIINS DECOMP")
  return out


def generate_action_sector(act_desp, persona, maze): 
  """TODO 
  Given the persona and the task description, choose the action_sector. 

  Persona state: identity stable set, n-1 day schedule, daily plan

  INPUT: 
    act_desp: description of the new action (e.g., "sleeping")
    persona: The Persona class instance 
  OUTPUT: 
    action_arena (e.g., "bedroom 2")
  EXAMPLE OUTPUT: 
    "bedroom 2"
  """
  if debug: print ("GNS FUNCTION: <generate_action_sector>")
  return run_gpt_prompt_action_sector(act_desp, persona, maze)[0]


def generate_action_arena(act_desp, persona, maze, act_world, act_sector): 
  """TODO 
  Given the persona and the task description, choose the action_arena. 

  Persona state: identity stable set, n-1 day schedule, daily plan

  INPUT: 
    act_desp: description of the new action (e.g., "sleeping")
    persona: The Persona class instance 
  OUTPUT: 
    action_arena (e.g., "bedroom 2")
  EXAMPLE OUTPUT: 
    "bedroom 2"
  """
  if debug: print ("GNS FUNCTION: <generate_action_arena>")
  return run_gpt_prompt_action_arena(act_desp, persona, maze, act_world, act_sector)[0]


def generate_action_game_object(act_desp, act_address, persona, maze):
  """TODO
  Given the action description and the act address (the address where
  we expect the action to task place), choose one of the game objects. 

  Persona state: identity stable set, n-1 day schedule, daily plan

  INPUT: 
    act_desp: the description of the action (e.g., "sleeping")
    act_address: the arena where the action will take place: 
               (e.g., "dolores double studio:double studio:bedroom 2")
    persona: The Persona class instance 
  OUTPUT: 
    act_game_object: 
  EXAMPLE OUTPUT: 
    "bed"
  """
  if debug: print ("GNS FUNCTION: <generate_action_game_object>")
  if not persona.s_mem.get_str_accessible_arena_game_objects(act_address): 
    return "<random>"
  return run_gpt_prompt_action_game_object(act_desp, persona, maze, act_address)[0]


def generate_action_pronunciatio(act_desp, persona): 
  """TODO 
  Given an action description, creates an emoji string description via a few
  shot prompt. 

  Does not really need any information from persona. 

  INPUT: 
    act_desp: the description of the action (e.g., "sleeping")
    persona: The Persona class instance
  OUTPUT: 
    a string of emoji that translates action description.
  EXAMPLE OUTPUT: 
    "🧈🍞"
  """
  if debug: print ("GNS FUNCTION: <generate_action_pronunciatio>")
  try: 
    x = run_gpt_prompt_pronunciatio(act_desp, persona)[0]
  except: 
    x = "🙂"

  if not x: 
    return "🙂"
  return x


def generate_action_event_triple(act_desp, persona): 
  """TODO 

  INPUT: 
    act_desp: the description of the action (e.g., "sleeping")
    persona: The Persona class instance
  OUTPUT: 
    a string of emoji that translates action description.
  EXAMPLE OUTPUT: 
    "🧈🍞"
  """
  if debug: print ("GNS FUNCTION: <generate_action_event_triple>")
  return run_gpt_prompt_event_triple(act_desp, persona)[0]


def generate_act_obj_desc(act_game_object, act_desp, persona): 
  if debug: print ("GNS FUNCTION: <generate_act_obj_desc>")
  return run_gpt_prompt_act_obj_desc(act_game_object, act_desp, persona)[0]


def generate_act_obj_event_triple(act_game_object, act_obj_desc, persona): 
  if debug: print ("GNS FUNCTION: <generate_act_obj_event_triple>")
  return run_gpt_prompt_act_obj_event_triple(act_game_object, act_obj_desc, persona)[0]


def generate_convo(maze, init_persona, target_persona): 
  curr_loc = maze.access_tile(init_persona.scratch.curr_tile)

  # convo = run_gpt_prompt_create_conversation(init_persona, target_persona, curr_loc)[0]
  # convo = agent_chat_v1(maze, init_persona, target_persona)
  #convo = agent_chat_v2(maze, init_persona, target_persona)
  #print("V2 ="+ str(convo))
  convo = agent_chat_v3(maze, init_persona, target_persona)
  #print("V3 = " + str(convo))
  final_convo = []
  appointment = None
  #print("CONVOOOOOO === " + str(convo))
  for row in convo:
    if row[0] == "appointment":
      #acrescentar o appointment
      appointment = row
    else:
      final_convo.append(row)
  #magic numbers from original devs? need to check dis
  convo_length = math.ceil(int(len(final_convo)))
  print("CONVO LENGTH = " + str(convo_length))
  #convo_length = 1
  if convo_length is None:
    convo_length = 1

  if debug: print ("GNS FUNCTION: <generate_convo>")
  return final_convo, appointment, convo_length

def generate_convo_robot(init_persona, target_persona, retrieved): 
  total_chat = []
  for utt in retrieved:
    if (init_persona.name in utt or target_persona.name in utt) and ":" in utt:
      chat = utt.split(":")[-1]
      if init_persona.name +" says:" in utt:
        name = init_persona.name
      elif target_persona.name +" says:" in utt:
        name = target_persona.name
      else:
        name="Someone"
    total_chat.append([name, chat])
  
  
  convo = agent_chat_v2_robot(init_persona, target_persona, total_chat)
  all_utt = ""

  for row in convo: 
    speaker = row[0]
    utt = row[1]
    all_utt += f"{speaker}: {utt}\n"

  convo_length = math.ceil(int(len(all_utt)/8) / 30)

  if debug: print ("GNS FUNCTION: <generate_convo>")
  return convo, convo_length


def generate_convo_summary(persona, convo, desc):
  #print("DESC 2= " + str(desc))
  convo_summary = run_gpt_prompt_summarize_conversation(persona, convo, desc=desc)[0]
  return convo_summary


def generate_decide_to_talk(init_persona, target_persona, retrieved):

  x =run_gpt_prompt_decide_to_talk(init_persona, target_persona, retrieved)[0]
  if debug: print ("GNS FUNCTION: <generate_decide_to_talk>")

  if x == "yes": 
    return True
  else: 
    return False


def generate_decide_to_react(init_persona, target_persona, retrieved): 
  if debug: print ("GNS FUNCTION: <generate_decide_to_react>")
  return run_gpt_prompt_decide_to_react(init_persona, target_persona, retrieved)[0]


def generate_new_decomp_schedule(persona, inserted_act, inserted_act_dur,  start_hour, end_hour): 
  # Step 1: Setting up the core variables for the function. 
  # <p> is the persona whose schedule we are editing right now. 
  p = persona
  # <today_min_pass> indicates the number of minutes that have passed today. 
  today_min_pass = (int(p.scratch.curr_time.hour) * 60 
                    + int(p.scratch.curr_time.minute) + 1)
  
  # Step 2: We need to create <main_act_dur> and <truncated_act_dur>. 
  # These are basically a sub-component of <f_daily_schedule> of the persona,
  # but focusing on the current decomposition. 
  # Here is an example for <main_act_dur>: 
  # ['wakes up and completes her morning routine (wakes up at 6am)', 5]
  # ['wakes up and completes her morning routine (wakes up at 6am)', 5]
  # ['wakes up and completes her morning routine (uses the restroom)', 5]
  # ['wakes up and completes her morning routine (washes her ...)', 10]
  # ['wakes up and completes her morning routine (makes her bed)', 5]
  # ['wakes up and completes her morning routine (eats breakfast)', 15]
  # ['wakes up and completes her morning routine (gets dressed)', 10]
  # ['wakes up and completes her morning routine (leaves her ...)', 5]
  # ['wakes up and completes her morning routine (starts her ...)', 5]
  # ['preparing for her day (waking up at 6am)', 5]
  # ['preparing for her day (making her bed)', 5]
  # ['preparing for her day (taking a shower)', 15]
  # ['preparing for her day (getting dressed)', 5]
  # ['preparing for her day (eating breakfast)', 10]
  # ['preparing for her day (brushing her teeth)', 5]
  # ['preparing for her day (making coffee)', 5]
  # ['preparing for her day (checking her email)', 5]
  # ['preparing for her day (starting to work on her painting)', 5]
  # 
  # And <truncated_act_dur> concerns only until where an event happens. 
  # ['wakes up and completes her morning routine (wakes up at 6am)', 5]
  # ['wakes up and completes her morning routine (wakes up at 6am)', 2]
  main_act_dur = []
  truncated_act_dur = []
  dur_sum = 0 # duration sum
  count = 0 # enumerate count
  truncated_fin = False 

  ##print ("DEBUG::: ", persona.scratch.name)
  for act, dur in p.scratch.f_daily_schedule: 
    if (dur_sum >= start_hour * 60) and (dur_sum < end_hour * 60): 
      main_act_dur += [[act, dur]]
      if dur_sum <= today_min_pass:
        truncated_act_dur += [[act, dur]]
      elif dur_sum > today_min_pass and not truncated_fin: 
        # We need to insert that last act, duration list like this one: 
        # e.g., ['wakes up and completes her morning routine (wakes up...)', 2]
        truncated_act_dur += [[p.scratch.f_daily_schedule[count][0], 
                               dur_sum - today_min_pass]] 
        truncated_act_dur[-1][-1] -= (dur_sum - today_min_pass) ######## DEC 7 DEBUG;.. is the +1 the right thing to do??? 
        # truncated_act_dur[-1][-1] -= (dur_sum - today_min_pass + 1) ######## DEC 7 DEBUG;.. is the +1 the right thing to do??? 
        ##print ("DEBUG::: ", truncated_act_dur)

        # truncated_act_dur[-1][-1] -= (dur_sum - today_min_pass) ######## DEC 7 DEBUG;.. is the +1 the right thing to do??? 
        truncated_fin = True
    dur_sum += dur
    count += 1

  persona_name = persona.name 
  main_act_dur = main_act_dur

  x = truncated_act_dur[-1][0].split("(")[0].strip() + " (on the way to " + truncated_act_dur[-1][0].split("(")[-1][:-1] + ")"
  truncated_act_dur[-1][0] = x 

  if "(" in truncated_act_dur[-1][0]: 
    inserted_act = truncated_act_dur[-1][0].split("(")[0].strip() + " (" + inserted_act + ")"

  # To do inserted_act_dur+1 below is an important decision but I'm not sure
  # if I understand the full extent of its implications. Might want to 
  # revisit. 
  truncated_act_dur += [[inserted_act, inserted_act_dur]]
  start_time_hour = (datetime.datetime(2022, 10, 31, 0, 0) 
                   + datetime.timedelta(hours=start_hour))
  end_time_hour = (datetime.datetime(2022, 10, 31, 0, 0) 
                   + datetime.timedelta(hours=end_hour))

  if debug: print ("GNS FUNCTION: <generate_new_decomp_schedule>")
  return run_gpt_prompt_new_decomp_schedule(persona, 
                                            main_act_dur, 
                                            truncated_act_dur, 
                                            start_time_hour,
                                            end_time_hour,
                                            inserted_act,
                                            inserted_act_dur)[0]


##############################################################################
# CHAPTER 3: Plan
##############################################################################

def revise_identity(persona): 
  p_name = persona.scratch.name

  #print(Fore.YELLOW)
  #print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n\n\n\n\n\n\n\n\t\t\t\REVISE\n\n\n\n\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
  #print(Style.RESET_ALL)
  focal_points = [f"{p_name}'s plan for {persona.scratch.curr_time.strftime('%A %B %d')}.",
                  f"Important recent events for {p_name}'s life."]
  retrieved = new_retrieve(persona, focal_points)

  statements = "[Statements]\n"
  for key, val in retrieved.items():
    for i in val: 
      statements += f"{i.created.strftime('%A %B %d -- %H:%M %p')}: {i.embedding_key}\n"
  # #print (";adjhfno;asdjao;idfjo;af", p_name)
  plan_prompt = statements + "\n"
  plan_prompt+= f"{persona.calendar.get_appointments(persona.scratch)}"
  plan_prompt += f"Given the statements above, is there anything that {p_name} should remember as they plan for"
  plan_prompt += f" *{persona.scratch.curr_time.strftime('%A %B %d')}*? Any new event you should attend, or obligation to keep?"
  plan_prompt += f"If there is any scheduling information, be as specific as possible (include date, time, and location if stated in the statement)\n\n"
  plan_prompt += f"Write the response from {p_name}'s perspective."
  plan_note = ChatGPT_single_request(plan_prompt)
  #print (plan_note)

  thought_prompt = statements + "\n"
  thought_prompt += f"Given the statements above, how might we summarize {p_name}'s feelings about their days up to now?\n\n"
  thought_prompt += f"Write the response from {p_name}'s perspective."
  thought_note = ChatGPT_single_request(thought_prompt)
  #print (thought_note)

  currently_prompt = f"{p_name}'s status from {(persona.scratch.curr_time - datetime.timedelta(days=1)).strftime('%A %B %d')}:\n"
  currently_prompt += f"{persona.scratch.currently}\n\n"
  if persona.emotional:
    emotions = persona.emotional_layer.find_predominant_emotions(3)
    em_descrs = [em.get_description(persona.name) for em in emotions]
    em_str = ""
    for descr in em_descrs:
      em_str += descr+"\n"
    currently_prompt += f"{em_str}"

  currently_prompt += f"{p_name}'s thoughts at the end of {(persona.scratch.curr_time - datetime.timedelta(days=1)).strftime('%A %B %d')}:\n" 
  currently_prompt += (plan_note + thought_note).replace('\n', '') + "\n\n"
  currently_prompt += f"It is now {persona.scratch.curr_time.strftime('%A %B %d')}. Given the above, write {p_name}'s status for {persona.scratch.curr_time.strftime('%A %B %d')} that reflects {p_name}'s thoughts at the end of {(persona.scratch.curr_time - datetime.timedelta(days=1)).strftime('%A %B %d')}. Write this in third-person past tense talking about {p_name}."
  currently_prompt += f"If there is any scheduling information, be as specific as possible (include the name of the event, date, time, and location if stated in the statement).\n\n"
  currently_prompt += "Follow this format below:\nStatus: <new status>"
  #print ("DEBUG NEW CURRENTLY", p_name)
  # #print (currently_prompt)
  new_currently = ChatGPT_single_request(currently_prompt)
  #print (new_currently)
  # #print (new_currently[10:])

  persona.scratch.currently = new_currently

  daily_req_prompt = f"Today is {persona.scratch.curr_time.strftime('%A %B %d')}. Is this a special day? Is there any different name for this day, or is it a normal one?"
  daily_req_prompt += f"Here's the status of {persona.name}'s reflections on the next day -- " + persona.scratch.currently + "\n"
  daily_req_prompt += f"Here is their usual lifestyle: {persona.scratch.lifestyle}."
  daily_req_prompt += f"{persona.calendar.get_appointments(persona.scratch)}"
  daily_req_prompt += f"Please respond with {persona.scratch.name}'s plan today in broad-strokes, by adding the new events from the reflection status (with the time of the day. e.g., have a lunch at 12:00 pm, watch TV from 7 to 8 pm).\n\n"
  daily_req_prompt += f"Follow this format (the list should have 4~6 items but no more):\n"
  daily_req_prompt += f"1. wake up and complete the morning routine at <time>, 2. ..."

  new_daily_req = ChatGPT_single_request(daily_req_prompt)
  new_daily_req = new_daily_req.replace('\n', ' ')
  new_daily_req = re.split(r"\d+\.", new_daily_req)
  final = []
  for i in range(len(new_daily_req)):
    if new_daily_req[i] != "":
      final.append(new_daily_req[i].strip())

  #print ("WE ARE HERE!!!", final)
  persona.scratch.daily_plan_req = final

def get_remaining_plan(persona):
  curr_f_org_index = persona.scratch.get_f_daily_schedule_hourly_org_index()
  all_indices = []
  # if curr_f_org_index > 0: 
  #   all_indices += [curr_f_org_index-1]
  all_indices += [curr_f_org_index]
  for i in range(len(persona.scratch.f_daily_schedule_hourly_org)):
    if curr_f_org_index+i <= len(persona.scratch.f_daily_schedule_hourly_org): 
      all_indices += [curr_f_org_index+i]
    else:
      break
 

  summ_str = f'Today is {persona.scratch.curr_time.strftime("%B %d, %Y")}. '
  summ_str += f'From '
  for index in all_indices: 
    #print ("index", index)
    if index < len(persona.scratch.f_daily_schedule_hourly_org): 
      start_min = 0
      for i in range(index): 
        start_min += persona.scratch.f_daily_schedule_hourly_org[i][1]
      end_min = start_min + persona.scratch.f_daily_schedule_hourly_org[index][1]
      start_time = (datetime.datetime.strptime("00:00:00", "%H:%M:%S") 
                    + datetime.timedelta(minutes=start_min)) 
      end_time = (datetime.datetime.strptime("00:00:00", "%H:%M:%S") 
                    + datetime.timedelta(minutes=end_min)) 
      start_time_str = start_time.strftime("%H:%M%p")
      end_time_str = end_time.strftime("%H:%M%p")
      summ_str += f"{start_time_str} ~ {end_time_str}, {persona.name} is planning on {persona.scratch.f_daily_schedule_hourly_org[index][0]}, "
      if curr_f_org_index+1 == index:
        curr_time_range = f'{start_time_str} ~ {end_time_str}'
  summ_str = summ_str[:-2] + "."

  return summ_str, all_indices


def coping_revise_plan(persona, old_desc, predominant_emotion, coping_strat):
  p_name = persona.scratch.name

  '''print(Fore.YELLOW)
  print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n\n\n\n\n\n\n\n\t\t\t\REVISE\n\n\n\n\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
  print(Style.RESET_ALL)'''

  remaining_plan, indices = get_remaining_plan(persona)


  coping_addon = f"""{old_desc}
But they are coping with this emotion by developping new plans to remove the problem that's causing them to feel this negative emotion. 
"""

  daily_req_prompt = f"Today is {persona.scratch.curr_time.strftime('%A %B %d')}."
  daily_req_prompt += f"Here's the status of {persona.name}'s reflections on the next day -- " + persona.scratch.currently + "\n"
  daily_req_prompt += f"{persona.calendar.get_appointments(persona.scratch)}"
  daily_req_prompt += f"Here is their old plan: {remaining_plan}."
  daily_req_prompt += coping_addon +"\n"
  daily_req_prompt += f"Please respond with {persona.scratch.name}'s new plan for the rest of the day (in broad-strokes) to remove the problem that is causing the negative {predominant_emotion.name} they feel. (with the time of the day. e.g., have a lunch at 12:00 pm, watch TV from 7 to 8 pm).\n\n"
  daily_req_prompt += f"Follow this format (the list should have 2~3 items but no more):\n"
  daily_req_prompt += f"1. {persona.scratch.f_daily_schedule_hourly_org[indices[0]-1][0]}, 2. ..."

  new_daily_req = ChatGPT_single_request(daily_req_prompt)
  new_daily_req = new_daily_req.replace('\n', ' ')
  new_daily_req = re.split(r"\d+\.", new_daily_req)
  final = [f"{persona.scratch.f_daily_schedule_hourly_org[indices[0]-1][0]}" ]
  for i in range(len(new_daily_req)):
    if new_daily_req[i] != "":
      final.append(new_daily_req[i].strip())

  

  #print ("WE ARE HERE!!!", final)
  persona.scratch.daily_plan_req = final
  return indices


def _long_term_planning(persona, new_day): 
  """
  Formulates the persona's daily long-term plan if it is the start of a new 
  day. This basically has two components: first, we create the wake-up hour, 
  and second, we create the hourly schedule based on it. 
  INPUT
    new_day: Indicates whether the current time signals a "First day",
             "New day", or False (for neither). This is important because we
             create the personas' long term planning on the new day. 
  """
  # We start by creating the wake up hour for the persona. 
  wake_up_hour = generate_wake_up_hour(persona)

  # When it is a new day, we start by creating the daily_req of the persona.
  # Note that the daily_req is a list of strings that describe the persona's
  # day in broad strokes.
  if new_day == "First day": 
    # Bootstrapping the daily plan for the start of then generation:
    # if this is the start of generation (so there is no previous day's 
    # daily requirement, or if we are on a new day, we want to create a new
    # set of daily requirements.
    persona.scratch.daily_req = generate_first_daily_plan(persona, 
                                                          wake_up_hour)
  elif new_day == "New day":
    revise_identity(persona)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - TODO
    # We need to create a new daily_req here...
    #print("BEFORE = " + str(persona.scratch.daily_req))
    persona.scratch.daily_req = persona.scratch.daily_plan_req
    #print("AFTER = " + str(persona.scratch.daily_req))

  # Based on the daily_req, we create an hourly schedule for the persona, 
  # which is a list of todo items with a time duration (in minutes) that 
  # add up to 24 hours.
  persona.scratch.f_daily_schedule = generate_hourly_schedule(persona, 
                                                              wake_up_hour)
  persona.scratch.f_daily_schedule_hourly_org = (persona.scratch
                                                   .f_daily_schedule[:])
  
  #print("NEW PLAN = " + str(persona.scratch.f_daily_schedule))


  # Added March 4 -- adding plan to the memory.
  thought = f"This is {persona.scratch.name}'s plan for {persona.scratch.curr_time.strftime('%A %B %d')}:"
  for i in persona.scratch.daily_req: 
    thought += f" {i},"
  thought = thought[:-1] + "."
  created = persona.scratch.curr_time
  expiration = persona.scratch.curr_time + datetime.timedelta(days=30)
  s, p, o = (persona.scratch.name, "plan", persona.scratch.curr_time.strftime('%A %B %d'))
  keywords = set(["plan"])
  thought_poignancy = 5
  thought_embedding_pair = (thought, get_embedding(thought))
  persona.a_mem.add_thought(created, expiration, s, p, o, 
                            thought, keywords, thought_poignancy, 
                            thought_embedding_pair, None)

  # #print("Sleeping for 20 seconds...")
  # time.sleep(10)
  # #print("Done sleeping!")



def _determine_action(persona, maze): 
  """
  Creates the next action sequence for the persona. 
  The main goal of this function is to run "add_new_action" on the persona's 
  scratch space, which sets up all the action related variables for the next 
  action. 
  As a part of this, the persona may need to decompose its hourly schedule as 
  needed.   
  INPUT
    persona: Current <Persona> instance whose action we are determining. 
    maze: Current <Maze> instance. 
  """
  def determine_decomp(act_desp, act_dura):
    """
    Given an action description and its duration, we determine whether we need
    to decompose it. If the action is about the agent sleeping, we generally
    do not want to decompose it, so that's what we catch here. 

    INPUT: 
      act_desp: the description of the action (e.g., "sleeping")
      act_dura: the duration of the action in minutes. 
    OUTPUT: 
      a boolean. True if we need to decompose, False otherwise. 
    """
    if "sleep" not in act_desp and "bed" not in act_desp: 
      return True
    elif "sleeping" in act_desp or "asleep" in act_desp or "in bed" in act_desp:
      return False
    elif "sleep" in act_desp or "bed" in act_desp: 
      if act_dura > 60: 
        return False
    return True

  # The goal of this function is to get us the action associated with 
  # <curr_index>. As a part of this, we may need to decompose some large 
  # chunk actions. 
  # Importantly, we try to decompose at least two hours worth of schedule at
  # any given point. 
  curr_index = persona.scratch.get_f_daily_schedule_index()
  curr_index_60 = persona.scratch.get_f_daily_schedule_index(advance=60)
  


  
  ##print("DETERMINE ACTION???")
  
     
    
    
  

    # * Decompose * 
    # During the first hour of the day, we need to decompose two hours 
    # sequence. We do that here. 
  if curr_index == 0:
    # This portion is invoked if it is the first hour of the day. 
    act_desp, act_dura = persona.scratch.f_daily_schedule[curr_index]
    if act_dura >= 60: 
      # We decompose if the next action is longer than an hour, and fits the
      # criteria described in determine_decomp.
      if determine_decomp(act_desp, act_dura): 
        persona.scratch.f_daily_schedule[curr_index:curr_index+1] = (
                            generate_task_decomp(persona, act_desp, act_dura))
    if curr_index_60 + 1 < len(persona.scratch.f_daily_schedule):
      act_desp, act_dura = persona.scratch.f_daily_schedule[curr_index_60+1]
      if act_dura >= 60: 
        if determine_decomp(act_desp, act_dura): 
          persona.scratch.f_daily_schedule[curr_index_60+1:curr_index_60+2] = (
                            generate_task_decomp(persona, act_desp, act_dura))

  if curr_index_60 < len(persona.scratch.f_daily_schedule):
    # If it is not the first hour of the day, this is always invoked (it is
    # also invoked during the first hour of the day -- to double up so we can
    # decompose two hours in one go). Of course, we need to have something to
    # decompose as well, so we check for that too. 
    if persona.scratch.curr_time.hour < 23:
      # And we don't want to decompose after 11 pm. 
      act_desp, act_dura = persona.scratch.f_daily_schedule[curr_index_60]
      if act_dura >= 60: 
        if determine_decomp(act_desp, act_dura): 
          persona.scratch.f_daily_schedule[curr_index_60:curr_index_60+1] = (
                              generate_task_decomp(persona, act_desp, act_dura))
  # * End of Decompose * 

  # Generate an <Action> instance from the action description and duration. By
  # this point, we assume that all the relevant actions are decomposed and 
  # ready in f_daily_schedule. 



  # 1440
  x_emergency = 0
  for i in persona.scratch.f_daily_schedule:
    #if persona.name=="Pepper Robot":
      #print(i)
    if i[1] is not None:
      x_emergency += i[1]
  ##print ("x_emergency", x_emergency)

  if 1440 - x_emergency > 0: 
    ##print ("x_emergency__AAA", x_emergency)
    persona.scratch.f_daily_schedule += [["sleeping", 1440 - x_emergency]]

  for elem in persona.scratch.f_daily_schedule:
    ##print(elem)
    if elem[1]==0:
      ##print("HERE")
      index = persona.scratch.f_daily_schedule.index(elem)
      persona.scratch.f_daily_schedule.pop(index)
  ##print("Ened")

  #print ("DEBUG Determine Action")
  #for i in persona.scratch.f_daily_schedule: print (i)
  #print (curr_index)
  #print (len(persona.scratch.f_daily_schedule))
  #print (persona.scratch.name)
  #print ("------")


  act_desp, act_dura = persona.scratch.f_daily_schedule[curr_index] 
  if act_desp is not None and act_dura is not None:
    #print("OLE")
    #print((act_desp, act_dura ))
    #print( persona.scratch.f_daily_schedule[curr_index])
    #print("OLE ===================")

    # Finding the target location of the action and creating action-related
    # variables.
    act_world = maze.access_tile(persona.scratch.curr_tile)["world"]
    # act_sector = maze.access_tile(persona.scratch.curr_tile)["sector"]
    act_sector = generate_action_sector(act_desp, persona, maze)
    act_arena = generate_action_arena(act_desp, persona, maze, act_world, act_sector)
    act_address = f"{act_world}:{act_sector}:{act_arena}"
    act_game_object = generate_action_game_object(act_desp, act_address,
                                                  persona, maze)
    new_address = f"{act_world}:{act_sector}:{act_arena}:{act_game_object}"
    act_pron = generate_action_pronunciatio(act_desp, persona)
    act_event = generate_action_event_triple(act_desp, persona)
    # Persona's actions also influence the object states. We set those up here. 
    act_obj_desp = generate_act_obj_desc(act_game_object, act_desp, persona)
    act_obj_pron = generate_action_pronunciatio(act_obj_desp, persona)
    act_obj_event = generate_act_obj_event_triple(act_game_object, 
                                                  act_obj_desp, persona)

    # Adding the action to persona's queue. 
    persona.scratch.add_new_action(new_address, 
                                  int(act_dura), 
                                  act_desp, 
                                  act_pron, 
                                  act_event,
                                  None,
                                  None,
                                  None,
                                  None,
                                  act_obj_desp, 
                                  act_obj_pron, 
                                  act_obj_event)


def _choose_retrieved(persona, retrieved): 
  """
  Retrieved elements have multiple core "curr_events". We need to choose one
  event to which we are going to react to. We pick that event here. 
  INPUT
    persona: Current <Persona> instance whose action we are determining. 
    retrieved: A dictionary of <ConceptNode> that were retrieved from the 
               the persona's associative memory. This dictionary takes the
               following form: 
               dictionary[event.description] = 
                 {["curr_event"] = <ConceptNode>, 
                  ["events"] = [<ConceptNode>, ...], 
                  ["thoughts"] = [<ConceptNode>, ...] }
  """
  # Once we are done with the reflection, we might want to build a more  
  # complex structure here.
  
  # We do not want to take self events... for now 
  
  copy_retrieved = retrieved.copy()
  for event_desc, rel_ctx in copy_retrieved.items(): 
    curr_event = rel_ctx["curr_event"]
    if curr_event.subject == persona.name: 
      del retrieved[event_desc]
  

  

  # Always choose persona first.
  priority = []
  for event_desc, rel_ctx in retrieved.items(): 
    #print(Fore.RED)
    #print(event_desc, rel_ctx)
    #print(Style.RESET_ALL)
    curr_event = rel_ctx["curr_event"]
    if (":" not in curr_event.subject
        and curr_event.subject != persona.name): 
      priority += [(event_desc, rel_ctx)]
  if priority:
    #if not persona.emotional:
      #return random.choice(priority)
    #else:
    priority.sort(key = lambda prio: prio[1]["intensity"], reverse=True)
    #print("PRIO ONE = " +str(priority))
    return priority[0]

  # Skip idle. 
  for event_desc, rel_ctx in retrieved.items(): 
    curr_event = rel_ctx["curr_event"]
    if "is idle" not in event_desc: 
      priority +=  [(event_desc, rel_ctx)]
  if priority: 
    #if not persona.emotional:
      #return random.choice(priority)
    #else:
    priority.sort(key = lambda prio: prio[1]["intensity"], reverse=True)
    #print("PRIO 2= " +str(priority))

    return priority[0]
  #print("CHOSE RETRIVED NONE")
  return None

def choose_target(curr_event, personas, persona, maze, index = -1):
  keys = list(personas.keys())
  elem = None
  
  '''for i in range(len(keys)):
    if i > index:
      k = keys[i]
      elem = personas[k]
      #print(elem)
      #print(elem.name)
      if elem.name in curr_event.description and elem.name != persona.name:
        return elem, i'''
      
  for i in range(len(keys)):
    if i > index:
      k = keys[i]
      elem = personas[k]
      '''
      curr_sector = f"{maze.access_tile(persona.scratch.curr_tile)['sector']}"
      curr_arena= f"{maze.access_tile(persona.scratch.curr_tile)['arena']}"
      curr_location = f"{curr_arena} in {curr_sector}"

      curr_sector = f"{maze.access_tile(elem.scratch.curr_tile)['sector']}"
      curr_arena= f"{maze.access_tile(elem.scratch.curr_tile)['arena']}"
      elem_curr_location = f"{curr_arena} in {curr_sector}"
      #curr_location == elem_curr_location and 
      '''

      dist = math.dist([elem.scratch.curr_tile[0], elem.scratch.curr_tile[1]], 
                        [persona.scratch.curr_tile[0], 
                        persona.scratch.curr_tile[1]])
      #print("DIST " + str(elem.name) + " = " + str(dist))
      #print("EVENT DIST = " + str(curr_event.dist))
      close = False
      # just a healthy margin +2
      if test_dialogue:
        if elem.name == "Klaus Mueller":
            return elem, i
      else:
        if dist <= persona.scratch.vision_r+2:
          close = True
          
          if close and elem.name != persona.name:
            return elem, i


  return None, i


def _should_react(persona, retrieved, personas, maze): 
  """
  Determines what form of reaction the persona should exihibit given the 
  retrieved values. 
  INPUT
    persona: Current <Persona> instance whose action we are determining. 
    retrieved: A dictionary of <ConceptNode> that were retrieved from the 
               the persona's associative memory. This dictionary takes the
               following form: 
               dictionary[event.description] = 
                 {["curr_event"] = <ConceptNode>, 
                  ["events"] = [<ConceptNode>, ...], 
                  ["thoughts"] = [<ConceptNode>, ...] }
    personas: A dictionary that contains all persona names as keys, and the 
              <Persona> instance as values. 
  """
  def lets_talk(init_persona, target_persona, retrieved):
    #print("LETS TALK RESULTS:")
    #print("Target ACT ADDRESS = " + str(target_persona.scratch.act_address))
    #print("target act descritpion = " + str(target_persona.scratch.act_description))
    #print("init act address = " + str(init_persona.scratch.act_address))
    #print("init description = " + str(init_persona.scratch.act_description))
    
    if (not target_persona.scratch.act_address 
        or not target_persona.scratch.act_description
        or not init_persona.scratch.act_address
        or not init_persona.scratch.act_description): 
      #print("NOT ADDRESS")  
      return False
    

    if ("sleeping" in target_persona.scratch.act_description 
        or "sleeping" in init_persona.scratch.act_description):
      #print("SLEEPING")
      return False

    if init_persona.scratch.curr_time.hour == 23:
      #print("ITS 23")
      return False

    if "<waiting>" in target_persona.scratch.act_address:
      #print("IS WAITING") 
      return False

    #print("init = " + str(init_persona.name))
    #print("target = " + str(target_persona.name))

    #print("init chatting with = " + str(init_persona.scratch.chatting_with))
    #print("target chatting with = " + str(target_persona.scratch.chatting_with))
    #print("init chatting with buffer = "+ str(init_persona.scratch.chatting_with_buffer))
    #print("target chatting with buffer = "+ str(target_persona.scratch.chatting_with_buffer))


    if (target_persona.scratch.chatting_with 
      or init_persona.scratch.chatting_with):
      #print("ALREADY CHATTING WTH")
      return False
    if (target_persona.name in init_persona.scratch.chatting_with_buffer): 
      if init_persona.scratch.chatting_with_buffer[target_persona.name] > 0: 
        #print("ALREADY CHATTING WTH 2 = " + str( init_persona.scratch.chatting_with_buffer))

        return False
    #print(init_persona.name)
    #print(target_persona.name)
    if init_persona.name != target_persona.name and generate_decide_to_talk(init_persona, target_persona, retrieved): 
      return True
    #print("LETS TALK NONE")
    return False

  def lets_react(init_persona, target_persona, retrieved): 
    if (not target_persona.scratch.act_address 
        or not target_persona.scratch.act_description
        or not init_persona.scratch.act_address
        or not init_persona.scratch.act_description): 
      return False

    if ("sleeping" in target_persona.scratch.act_description 
        or "sleeping" in init_persona.scratch.act_description): 
      return False

    # return False
    if init_persona.scratch.curr_time.hour == 23: 
      return False

    if "waiting" in target_persona.scratch.act_description: 
      return False
    if init_persona.scratch.planned_path == []:
      return False

    if (init_persona.scratch.act_address 
        != target_persona.scratch.act_address): 
      return False

    react_mode = generate_decide_to_react(init_persona, 
                                          target_persona, retrieved)

    if react_mode == "1": 
      wait_until = ((target_persona.scratch.act_start_time 
        + datetime.timedelta(minutes=target_persona.scratch.act_duration - 1))
        .strftime("%B %d, %Y, %H:%M:%S"))
      return f"wait: {wait_until}"
    elif react_mode == "2":
      return False
      return "do other things"
    else:
      return False #"keep" 
    
  #print("SHOULD REACT")

  # If the persona is chatting right now, default to no reaction 
  if persona.scratch.chatting_with:
    #print("HEWRE") 
    return False, None
  if "<waiting>" in persona.scratch.act_address: 
    #print("HEWRE 2") 

    return False, None

  # Recall that retrieved takes the following form: 
  # dictionary {["curr_event"] = <ConceptNode>, 
  #             ["events"] = [<ConceptNode>, ...], 
  #             ["thoughts"] = [<ConceptNode>, ...]}
  curr_event = retrieved["curr_event"]

  #print(personas)

  if "is idle" not in curr_event.description:
    index = -1
    #print("OLE")

    emotional_reaction = False

  
    if persona.emotional:
      react = persona.emotional_layer.get_reaction(persona)
      #print("EMOTIONAL REACT? = "+ str(react))
      if  react is not None and react[0] is not None and react[1] is not None:
        desc, dura = react
        #persona.scratch.f_daily_schedule.insert(curr_index, [desc, dura ])
        emotional_reaction = True
        #print("HEWRE 3") 

        return "emo", react
      #print("OLE 2")



    while index < len(personas.keys()) -1:
      target, index = choose_target(curr_event, personas, persona, maze, index)
      
      '''if target is not None:
        print("CHOSE TARGET = " + str(target.name) + ": " + str(index))
      else:
        print("CHOSE TARGET = " + str(target) + ": " + str(index))'''
      

        
      # this is a persona event. 
      if target is not None and lets_talk(persona, target, retrieved):
        #print("HEWRE 4") 

        return f"chat with {curr_event.subject}", None
      
      if target is not None:
        react_mode = lets_react(persona, target, 
                                retrieved)
        #print("HEWRE 5") 

        return react_mode, None
  #print("HEWRE 6") 

  return False, None


def _create_react(persona, inserted_act, inserted_act_dur,
                  act_address, act_event, chatting_with, chat, chatting_with_buffer,
                  chatting_end_time, 
                  act_pronunciatio, act_obj_description, act_obj_pronunciatio, 
                  act_obj_event, act_start_time=None): 
  p = persona 

  min_sum = 0
  for i in range (p.scratch.get_f_daily_schedule_hourly_org_index()): 
    min_sum += p.scratch.f_daily_schedule_hourly_org[i][1]
  start_hour = int (min_sum/60)

  if (p.scratch.f_daily_schedule_hourly_org[p.scratch.get_f_daily_schedule_hourly_org_index()][1] >= 120):
    end_hour = start_hour + p.scratch.f_daily_schedule_hourly_org[p.scratch.get_f_daily_schedule_hourly_org_index()][1]/60

  elif (p.scratch.f_daily_schedule_hourly_org[p.scratch.get_f_daily_schedule_hourly_org_index()][1] + 
      p.scratch.f_daily_schedule_hourly_org[p.scratch.get_f_daily_schedule_hourly_org_index()+1][1]): 
    end_hour = start_hour + ((p.scratch.f_daily_schedule_hourly_org[p.scratch.get_f_daily_schedule_hourly_org_index()][1] + 
              p.scratch.f_daily_schedule_hourly_org[p.scratch.get_f_daily_schedule_hourly_org_index()+1][1])/60)

  else: 
    end_hour = start_hour + 2
  end_hour = int(end_hour)

  dur_sum = 0
  count = 0 
  start_index = None
  end_index = None
  for act, dur in p.scratch.f_daily_schedule: 
    try:
      if dur_sum >= start_hour * 60 and start_index == None:
        start_index = count
      if dur_sum >= end_hour * 60 and end_index == None: 
        end_index = count
      dur_sum += dur
      count += 1
    except Exception as e:

      print(e)
      print((act, dur))
      raise e
      

  ret = generate_new_decomp_schedule(p, inserted_act, inserted_act_dur, 
                                       start_hour, end_hour)
  p.scratch.f_daily_schedule[start_index:end_index] = ret
  p.scratch.add_new_action(act_address,
                           inserted_act_dur,
                           inserted_act,
                           act_pronunciatio,
                           act_event,
                           chatting_with,
                           chat,
                           chatting_with_buffer,
                           chatting_end_time,
                           act_obj_description,
                           act_obj_pronunciatio,
                           act_obj_event,
                           act_start_time)
  



def _chat_react(maze, persona, focused_event, reaction_mode, personas):
  # There are two personas -- the persona who is initiating the conversation
  # and the persona who is the target. We get the persona instances here. 
  init_persona = persona
  target_persona, index = choose_target(focused_event, personas, persona, maze)
  curr_personas = [init_persona, target_persona]

  # Actually creating the conversation here. 
  convo, appointment, duration_min = generate_convo(maze, init_persona, target_persona)
  desc = None
  if init_persona.a_mem.seq_chat: 
      for i in init_persona.a_mem.seq_chat: 
        #print("SEQ CHAT = " + str(i.object))
        #print("TARGET = " + str(target_persona.name))
        if i.object == target_persona.name: 
          desc = i.description
          break
  if convo[0][0] == init_persona.name:
    first = init_persona
    second = target_persona
  else:
    first = target_persona
    second = init_persona
  final_convo = []
  pair = True
  for elem in convo:
    if pair:
      final_convo.append([first.name, elem[1]])
    else:
      final_convo.append([second.name, elem[1]])
    pair = not pair

  
  convo = final_convo

  #print("DESC = " + str(desc))
  convo_summary = generate_convo_summary(init_persona, convo, desc)
  inserted_act = convo_summary
  inserted_act_dur = duration_min

  act_start_time = target_persona.scratch.act_start_time

  curr_time = target_persona.scratch.curr_time
  if curr_time.second != 0: 
    temp_curr_time = curr_time + datetime.timedelta(seconds=60 - curr_time.second)
    chatting_end_time = temp_curr_time + datetime.timedelta(seconds=inserted_act_dur*SECS_PER_STEP)
  else: 
    chatting_end_time = curr_time + datetime.timedelta(seconds=inserted_act_dur*SECS_PER_STEP)
  agents = [("init", init_persona), ("target", target_persona)]
  c_length = len(convo)
  for role, p in agents:
    #print(role,p)
    if role == "init": 
      act_address = f"<persona> {target_persona.name}"
      act_event = (p.name, "chat with", target_persona.name)
      chatting_with = target_persona.name
      chatting_with_buffer = {}
      #magic number from the original devs btw
      chatting_with_buffer[target_persona.name] = c_length*2
    elif role == "target": 
      act_address = f"<persona> {init_persona.name}"
      act_event = (p.name, "chat with", init_persona.name)
      chatting_with = init_persona.name
      chatting_with_buffer = {}
      #magic number from the original devs btw
      chatting_with_buffer[init_persona.name] = c_length*2

    act_pronunciatio = "💬" 
    act_obj_description = None
    act_obj_pronunciatio = None
    act_obj_event = (None, None, None)

    _create_react(p, inserted_act, inserted_act_dur,
      act_address, act_event, chatting_with, convo, chatting_with_buffer, chatting_end_time,
      act_pronunciatio, act_obj_description, act_obj_pronunciatio, 
      act_obj_event, act_start_time)
    
    #print(appointment)

    if appointment is not None:
      if appointment[1]["name"] is not None:
        #print(p)
        _create_appointment(p, curr_personas, appointment[1])


def _create_appointment(ag, curr_personas, appointment):
  involved_people = [p.name for p in curr_personas]
  name = appointment["name"]
  location = appointment["location"]
  date_time = appointment["date_time"]
  description = appointment["description"]
  duration = appointment["duration"]
  people = involved_people
  #print("create appointment = " + str((name, location, date_time, people, description)))
  ag.calendar.create_appointment(name, location, date_time, people, description, duration)


def _wait_react(persona, reaction_mode): 
  p = persona

  inserted_act = f'waiting to start {p.scratch.act_description.split("(")[-1][:-1]}'
  end_time = datetime.datetime.strptime(reaction_mode[6:].strip(), "%B %d, %Y, %H:%M:%S")
  inserted_act_dur = (end_time.minute + end_time.hour * 60) - (p.scratch.curr_time.minute + p.scratch.curr_time.hour * 60) + 1

  act_address = f"<waiting> {p.scratch.curr_tile[0]} {p.scratch.curr_tile[1]}"
  act_event = (p.name, "waiting to start", p.scratch.act_description.split("(")[-1][:-1])
  chatting_with = None
  chat = None
  chatting_with_buffer = None
  chatting_end_time = None

  act_pronunciatio = "⌛" 
  act_obj_description = None
  act_obj_pronunciatio = None
  act_obj_event = (None, None, None)

  _create_react(p, inserted_act, inserted_act_dur,
    act_address, act_event, chatting_with, chat, chatting_with_buffer, chatting_end_time,
    act_pronunciatio, act_obj_description, act_obj_pronunciatio, act_obj_event)
  
def _emo_react(persona, action, duration): 
  p = persona

  inserted_act = action
  inserted_act_dur = duration

  act_address = f"{p.scratch.curr_tile[0]} {p.scratch.curr_tile[1]}"
  act_event = (p.name, "is reacting", "emotionally")
  chatting_with = None
  chat = None
  chatting_with_buffer = None
  chatting_end_time = None

  act_pronunciatio = "💬" 
  act_obj_description = None
  act_obj_pronunciatio = None
  act_obj_event = (None, None, None)

  _create_react(p, inserted_act, inserted_act_dur,
    act_address, act_event, chatting_with, chat, chatting_with_buffer, chatting_end_time,
    act_pronunciatio, act_obj_description, act_obj_pronunciatio, act_obj_event)
  

def coping(persona, focused_event, personas ):
  print("ACT DESCRIPTION = " + str(persona.scratch.act_description))
  #if True:
  if(persona.emotional and (persona.scratch.act_description is None or
              (persona.scratch.act_description is not None and "sleeping" not in persona.scratch.act_description))
                ):
        
        #print("HERE GENERATE APPRAISALS!!!")
        persona.emotional_layer.generate_appraisals( persona, personas)

        #coping here!!!!
        predominant_emotion = persona.emotional_layer.find_predominant_emotions(1)[0]
        old_desc = predominant_emotion.get_description(persona.name)
        ev = predominant_emotion.get_main_contribution()
        #print("PREDOMINANT = " + str(predominant_emotion))
        #print("VALENCE = " + str(predominant_emotion.valence))
        if predominant_emotion.valence == "Negative":
          #altera o 0 no futuro!
          #print("entrou aqui!")
          #print("")
          if predominant_emotion.value >= predominant_emotion.high_threshold:
            coping_strat = persona.emotional_layer.get_coping_strategy(predominant_emotion, persona)

            #coping_strat = persona.emotional_layer.coping_strategies.get("Planning")
            if coping_strat is not None:
              #print("COPING STRAT = "+ str(coping_strat))
              #print("COPING STRAT TYPE = " + str(coping_strat.type))
              coping_strat.upper_limit = predominant_emotion.value
              #if coping strat.type = "Emotion-Focused" - re-appraise - only single event
              if  coping_strat.type == "Emotion-Focused":
                #print("ENTRAMOS AQUI")

                persona.emotional_layer.generate_appraisals( persona, personas, predominant_emotion, coping_strat )
                new_predominant_emotion = persona.emotional_layer.find_predominant_emotions(1)[0]

                #ev is a contribution
                thought = f"The event '{ev[0][3]}' made {persona.name} feel {predominant_emotion.name}. But they coped with this feeling with {coping_strat.name}."

                if new_predominant_emotion != predominant_emotion:
                  thought+= f"Because of this, now they feel {new_predominant_emotion.name}."
                else:
                  thought+= f"Because of this, they feel more mildly about this event now."


              # if copingstrat.type = "Problem-Focused" - re-plan - only from curr_time forward!
              else:
                indices = coping_revise_plan(persona, old_desc, predominant_emotion, coping_strat)
                persona.scratch.daily_req[:indices[0]-1]
                for i in range(len(persona.scratch.daily_plan_req)):
                   persona.scratch.daily_req.append(persona.scratch.daily_plan_req[i])

                  #print("AFTER = " + str(persona.scratch.daily_req))

                # Based on the daily_req, we create an hourly schedule for the persona, 
                # which is a list of todo items with a time duration (in minutes) that 
                # add up to 24 hours.
                curr_index = persona.scratch.get_f_daily_schedule_index()

                new_schedule = coping_re_generate_hourly_schedule(persona)

                persona.scratch.f_daily_schedule = persona.scratch.f_daily_schedule[:curr_index]

                for elem in new_schedule:
                  persona.scratch.f_daily_schedule.append(elem)

                persona.scratch.f_daily_schedule_hourly_org = (persona.scratch
                                                                .f_daily_schedule[:])
                
                #print("NEW PLAN = " + str(persona.scratch.f_daily_schedule))
                #print("NEW PLAN 2 = " + str(persona.scratch.f_daily_schedule[curr_index:]))

                #print("focused event ="+str(focused_event))
                
                thought = f"The event '{ev[0][3]}' made {persona.name} feel {predominant_emotion.name}. But they coped with the situation by making a new plan to fix the situation. "
              


              created = persona.scratch.curr_time
              expiration = persona.scratch.curr_time + datetime.timedelta(days=30)
              s, p, o = (persona.scratch.name, "felt", predominant_emotion.name)
              keywords = set(["emotion"])
              thought_poignancy = 5
              thought_embedding_pair = (thought, get_embedding(thought))
              persona.a_mem.add_thought(created, expiration, s, p, o, 
                                        thought, keywords, thought_poignancy, 
                                        thought_embedding_pair, None)
              
              #persona.emotional_layer.print_layer()
              





def plan(persona, maze, personas, new_day, retrieved, event_triplet): 
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
  # PART 1: Generate the hourly schedule.
  was_reset=False

  
  if new_day or len(persona.scratch.f_daily_schedule) == 0:
    if len(persona.scratch.f_daily_schedule) == 0:
      was_reset=True
      new_day = "First day"
    #if persona.emotional:
      #persona.emotional_layer.generate_appraisals( event_triplet, persona, personas)
    _long_term_planning(persona, new_day)
  
  
  
  focused_event = False
  
  #remove later
  
  
  if persona.name == "Isabella Rodriguez" and test_dialogue:
    
    node = ConceptNode(9999999, 999999999, 1, None, 3,persona.scratch.curr_time, persona.scratch.curr_time, 
                        "Klaus Mueller", "chats with", persona.name, 
                        "Klaus Mueller said hello to " + persona.name + " and said he wanted to talk to her, about some thoughts he's having", None, 
                        0.8, [], None)
    event = ConceptNode(9999999, 999999999, 1, None, 3,persona.scratch.curr_time, persona.scratch.curr_time, 
                        "Klaus Mueller", "wants to", "chat", 
                        "idle", None, 
                        0.8, [], None)
    retrieved = {'Klaus Mueller has arrived': {'curr_event':event, 'events': [node,], "thoughts": [], 'intensity': 8.0}}
    #print("RETRIEVED = " + str(retrieved))
    
    
    
  
  if retrieved.keys(): 
    
    #print("NEW RETRIEVED =  "+ str(retrieved))
    focused_event = _choose_retrieved(persona, retrieved)
    if persona.emotional:
      persona.emotional_layer.focused_event = focused_event
        
    if focused_event is not None:
      #print("FOCUSED EVENT = " + str(focused_event[0]))
      focused_event = focused_event[1]

  coping(persona, focused_event, personas)
      


  # PART 2: If the current action has expired, we want to create a new plan.
  # or the emotional reaction layer has been triggered?

  if was_reset or persona.scratch.act_check_finished() or (persona.emotional and persona.emotional_layer.is_reaction_required()):
    #print("DETERMINE ACTION")
    _determine_action(persona, maze)

  # PART 3: If you perceived an event that needs to be responded to (saw 
  # another persona), and retrieved relevant information. 
  # Step 1: Retrieved may have multiple events represented in it. The first 
  #         job here is to determine which of the events we want to focus 
  #         on for the persona. 
  #         <focused_event> takes the form of a dictionary like this: 
  #         dictionary {["curr_event"] = <ConceptNode>, 
  #                     ["events"] = [<ConceptNode>, ...], 
  #                     ["thoughts"] = [<ConceptNode>, ...]}
        

  
  # Step 2: Once we choose an event, we need to determine whether the
  #         persona will take any actions for the perceived event. There are
  #         three possible modes of reaction returned by _should_react. 
  #         a) "chat with {target_persona.name}"
  #         b) "react"
  #         c) False

  if focused_event:
    print("FOCUSED EVENT = "+ str(focused_event["curr_event"]))
  else:
    print("NO FOCUSED EVENT")


  if focused_event:
    
    print("herevgdahgjasdhvg")

    stuff = _should_react(persona, focused_event, personas, maze)
    print(stuff)

    reaction_mode, emo_react = stuff
    


    if reaction_mode: 
      # If we do want to chat, then we generate conversation 

      if reaction_mode[:9] == "chat with":
        _chat_react(maze, persona, focused_event, reaction_mode, personas)
      elif reaction_mode[:4] == "wait": 
        _wait_react(persona, reaction_mode)
      elif reaction_mode == "emo":
        _emo_react(persona, emo_react[0], emo_react[1])
      # elif reaction_mode == "do other things": 
      #   _chat_react(persona, focused_event, reaction_mode, personas)

  persona.calendar.display_appointments(persona.calendar.get_current_appointments(persona.scratch), persona.scratch)
  # Step 3: Chat-related state clean up. 
  # If the persona is not chatting with anyone, we clean up any of the 
  # chat-related states here. 
  if persona.scratch.act_event[1] != "chat with":
    persona.scratch.chatting_with = None
    persona.scratch.chat = None
    persona.scratch.chatting_end_time = None
  # We want to make sure that the persona does not keep conversing with each
  # other in an infinite loop. So, chatting_with_buffer maintains a form of 
  # buffer that makes the persona wait from talking to the same target 
  # immediately after chatting once. We keep track of the buffer value here. 
  curr_persona_chat_buffer = persona.scratch.chatting_with_buffer
  remove_buff = []
  for persona_name, buffer_count in curr_persona_chat_buffer.items():
    if persona_name != persona.scratch.chatting_with: 
      persona.scratch.chatting_with_buffer[persona_name] -= 1
    if persona.scratch.chatting_with_buffer[persona_name] <=0:
      remove_buff.append(persona_name)
  
  for elem in remove_buff:
    #print(elem)
    del persona.scratch.chatting_with_buffer[elem]
  #print("BUFF AFTER DELETE = " + str(persona.scratch.chatting_with_buffer))

      

  #time.sleep(0.5)
  return persona.scratch.act_address











































 
