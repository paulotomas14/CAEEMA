"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: converse.py
Description: An extra cognitive module for generating conversations. 
"""
import math
import sys
import datetime
import random
from openai import OpenAI
sys.path.append('../')

from global_methods import *

from persona.memory_structures.spatial_memory import *
from persona.memory_structures.associative_memory import *
from persona.memory_structures.scratch import *
from persona.cognitive_modules.retrieve import *
from persona.prompt_template.run_gpt_prompt import *
from persona.cognitive_modules.variables import CHAT_SIMULATION_STEPS, NavelEmotion
from colorama import Fore, Style
from utils import openai_api_key
from utils import REPLACEMENT_NAME, DIALOGUE_MODEL
import string
MAX_LINES = 8
CUTOFF_SUMMARY = 4


def contains_punctuation(text):
    punctuation_marks = set(string.punctuation)
    #print("PUNC = " + str(punctuation_marks))
    punctuation_marks-= set([",", ";", ":", "'", "`", "-", "\""])



    #print(punctuation_marks)
    return any(char in punctuation_marks for char in text)




def generate_agent_chat_summarize_ideas(init_persona, 
                                        target_persona, 
                                        retrieved, 
                                        curr_context): 
  all_embedding_keys = list()
  for key, val in retrieved.items(): 
    for i in val: 
      all_embedding_keys += [i.embedding_key]
  all_embedding_key_str =""
  for i in all_embedding_keys: 
    all_embedding_key_str += f"{i}\n"

  try: 
    summarized_idea = run_gpt_prompt_agent_chat_summarize_ideas(init_persona,
                        target_persona, all_embedding_key_str, 
                        curr_context)[0]
  except:
    summarized_idea = ""
  return summarized_idea


def generate_summarize_agent_relationship(init_persona, 
                                          target_persona, 
                                          retrieved): 
  all_embedding_keys = list()
  for key, val in retrieved.items(): 
    for i in val: 
      all_embedding_keys += [i.embedding_key]
  all_embedding_key_str =""
  for i in all_embedding_keys: 
    all_embedding_key_str += f"{i}\n"

  summarized_relationship = run_gpt_prompt_agent_chat_summarize_relationship(
                              init_persona, target_persona,
                              all_embedding_key_str)[0]
  return summarized_relationship


def generate_agent_chat(maze, 
                        init_persona, 
                        target_persona,
                        curr_context, 
                        init_summ_idea, 
                        target_summ_idea): 
  summarized_idea = run_gpt_prompt_agent_chat(maze, 
                                              init_persona, 
                                              target_persona,
                                              curr_context, 
                                              init_summ_idea, 
                                              target_summ_idea)[0]
  #for i in summarized_idea: 
    ##print (i)
  return summarized_idea


def agent_chat_v1(maze, init_persona, target_persona): 
  # Chat version optimized for speed via batch generation
  curr_context = (f"{init_persona.scratch.name} " + 
              f"was {init_persona.scratch.act_description} " + 
              f"when {init_persona.scratch.name} " + 
              f"saw {target_persona.scratch.name} " + 
              f"in the middle of {target_persona.scratch.act_description}.\n")
  curr_context += (f"{init_persona.scratch.name} " +
              f"is thinking of initating a conversation with " +
              f"{target_persona.scratch.name}.")

  summarized_ideas = []
  part_pairs = [(init_persona, target_persona), 
                (target_persona, init_persona)]
  for p_1, p_2 in part_pairs: 
    focal_points = [f"{p_2.scratch.name}"]
    retrieved = new_retrieve(p_1, focal_points, 50)
    relationship = generate_summarize_agent_relationship(p_1, p_2, retrieved)
    focal_points = [f"{relationship}", 
                    f"{p_2.scratch.name} is {p_2.scratch.act_description}"]
    retrieved = new_retrieve(p_1, focal_points, 25)
    summarized_idea = generate_agent_chat_summarize_ideas(p_1, p_2, retrieved, curr_context)
    summarized_ideas += [summarized_idea]

  return generate_agent_chat(maze, init_persona, target_persona, 
                      curr_context, 
                      summarized_ideas[0], 
                      summarized_ideas[1])


def generate_utterances_robot( init_persona, target_persona, retrieved, curr_chat): 
  # Chat version optimized for speed via batch generation
  curr_context = (f"{init_persona.scratch.name} " + 
              f"was {init_persona.scratch.act_description} " + 
              f"when {init_persona.scratch.name} " + 
              f"saw {target_persona.scratch.name} " + 
              f"in the middle of {target_persona.scratch.act_description}.\n")
  curr_context += (f"{init_persona.scratch.name} " +
              f"is initiating a conversation with " +
              f"{target_persona.scratch.name}.")

  x = run_gpt_generate_iterative_chat_utt_robot(init_persona, target_persona, retrieved, curr_context, curr_chat)[0]

  return x["utterance"], x["end"]


def generate_one_utterance(maze, init_persona, target_persona, retrieved, curr_chat): 
  # Chat version optimized for speed via batch generation
  curr_context = (f"{init_persona.scratch.name} " + 
              f"was {init_persona.scratch.act_description} " + 
              f"when {init_persona.scratch.name} " + 
              f"saw {target_persona.scratch.name} " + 
              f"in the middle of {target_persona.scratch.act_description}.\n")
  curr_context += (f"{init_persona.scratch.name} " +
              f"is initiating a conversation with " +
              f"{target_persona.scratch.name}.")

  ##print ("July 23 5")
  x = run_gpt_generate_iterative_chat_utt(maze, init_persona, target_persona, retrieved, curr_context, curr_chat)[0]

  ##print ("July 23 6")

  ##print ("adshfoa;khdf;fajslkfjald;sdfa HERE", x)

  return x["utterance"], x["end"]

def agent_chat_v2(maze, init_persona, target_persona): 
  curr_chat = []
  ##print ("AGENT CHAT V2")

  for i in range(3): 
    focal_points = [f"{target_persona.scratch.name}"]
    retrieved = new_retrieve(init_persona, focal_points, 50)
    relationship = generate_summarize_agent_relationship(init_persona, target_persona, retrieved)
    ##print ("-------- relationshopadsjfhkalsdjf", relationship)
    last_chat = ""
    for i in curr_chat[-4:]:
      last_chat += ": ".join(i) + "\n"
    if last_chat: 
      focal_points = [f"{relationship}", 
                      f"{target_persona.scratch.name} is {target_persona.scratch.act_description}", 
                      last_chat]
    else: 
      focal_points = [f"{relationship}", 
                      f"{target_persona.scratch.name} is {target_persona.scratch.act_description}"]
    retrieved = new_retrieve(init_persona, focal_points, 15)
    utt, end = generate_one_utterance(maze, init_persona, target_persona, retrieved, curr_chat)

    curr_chat += [[init_persona.scratch.name, utt]]
    if end:
      break


    focal_points = [f"{init_persona.scratch.name}"]
    retrieved = new_retrieve(target_persona, focal_points, 50)
    relationship = generate_summarize_agent_relationship(target_persona, init_persona, retrieved)
    ##print ("-------- relationshopadsjfhkalsdjf", relationship)
    last_chat = ""
    for i in curr_chat[-4:]:
      last_chat += ": ".join(i) + "\n"
    if last_chat: 
      focal_points = [f"{relationship}", 
                      f"{init_persona.scratch.name} is {init_persona.scratch.act_description}", 
                      last_chat]
    else: 
      focal_points = [f"{relationship}", 
                      f"{init_persona.scratch.name} is {init_persona.scratch.act_description}"]
    retrieved = new_retrieve(target_persona, focal_points, 15)
    utt, end = generate_one_utterance(maze, target_persona, init_persona, retrieved, curr_chat)

    curr_chat += [[target_persona.scratch.name, utt]]
    if end:
      break

  '''#print ("July 23 PU")
  for row in curr_chat: 
    #print (row)
  #print ("July 23 FIN")'''
  ##print ("AGENT CHAT V2 ENDED")


  return curr_chat

def generate_all_utterances(maze, init_persona, target_persona, retrieved_init_p, retrieved_target_p): 
  # Chat version optimized for speed via batch generation
  curr_context = (f"{init_persona.scratch.name} " + 
              f"was {init_persona.scratch.act_description} " + 
              f"when {init_persona.scratch.name} " + 
              f"saw {target_persona.scratch.name} " + 
              f"in the middle of {target_persona.scratch.act_description}.\n")
  curr_context += (f"{init_persona.scratch.name} " +
              f"is initiating a conversation with " +
              f"{target_persona.scratch.name}.")
  
  
  


  ##print ("July 23 5")
  x = run_gpt_generate_all_chat_utt(maze, init_persona, target_persona, retrieved_init_p, retrieved_target_p, curr_context)[0]

  ##print ("July 23 6")

  ##print ("adshfoa;khdf;fajslkfjald;sdfa HERE", x)

  return x


def agent_chat_v3(maze, init_persona, target_persona): 
  curr_chat = []
  print ("AGENT CHAT V3")

  focal_points = [f"{init_persona.scratch.name}"]
  retrieved = new_retrieve(target_persona, focal_points, 15)
  relationship_init_persona = generate_summarize_agent_relationship(init_persona, target_persona, retrieved)
  focal_points_init = [f"{relationship_init_persona}", 
                    f"{target_persona.scratch.name} is {target_persona.scratch.act_description}"]
  retrieved_init_persona = new_retrieve(init_persona, focal_points_init, 10)
  

  focal_points = [f"{target_persona.scratch.name}"]
  retrieved = new_retrieve(target_persona, focal_points, 15)
  relationship_target_persona = generate_summarize_agent_relationship(target_persona, init_persona, retrieved)

  focal_points_target = [f"{relationship_target_persona}", 
                    f"{init_persona.scratch.name} is {init_persona.scratch.act_description}"]
  retrieved_target_persona = new_retrieve(target_persona, focal_points_target, 10)
  
  
    

  curr_chat = generate_all_utterances(maze, init_persona, target_persona, retrieved_init_persona, retrieved_target_persona)
  

  '''#print ("July 23 PU")
  for row in curr_chat: 
    #print (row)
  #print ("July 23 FIN")'''
  ##print ("AGENT CHAT V2 ENDED")


  return curr_chat





def agent_chat_v2_robot(init_persona, target_persona, curr_chat): 
  focal_points = [f"{target_persona.scratch.name}"]
  retrieved = new_retrieve(init_persona, focal_points, 50)
  relationship = generate_summarize_agent_relationship(init_persona, target_persona, retrieved)
  last_chat = ""
  #print(curr_chat)
  ##print(len(curr_chat))
  ##print(len(curr_chat[-4:]))
  for i in curr_chat[-4:]:
    last_chat += ": ".join(i) + "\n"
  if last_chat: 
    focal_points = [f"{relationship}", 
                    f"{target_persona.scratch.name} is {target_persona.scratch.act_description}", 
                    last_chat]
  else: 
    focal_points = [f"{relationship}", 
                    f"{target_persona.scratch.name} is {target_persona.scratch.act_description}"]
  retrieved = new_retrieve(init_persona, focal_points, 15)
  utt, end = generate_utterances_robot(init_persona, target_persona, retrieved, curr_chat)

  curr_chat += [[init_persona.scratch.name, utt]]

  for row in curr_chat: 
    print (row)

  return curr_chat





def generate_summarize_ideas(persona, nodes, question, partner): 
  statements = ""
  for n in nodes:
    statements += f"{n.embedding_key}\n"
  summarized_idea = run_gpt_prompt_summarize_ideas(persona, statements, question, partner)[0]
  return summarized_idea


def generate_next_line(persona, interlocutor_desc, curr_convo, summarized_idea):
  # Original chat -- line by line generation 
  prev_convo = ""
  for row in curr_convo: 
    prev_convo += f'{row[0]}: {row[1]}\n'

  next_line = run_gpt_prompt_generate_next_convo_line(persona, 
                                                      interlocutor_desc, 
                                                      prev_convo, 
                                                      summarized_idea)[0]  
  return next_line

def generate_next_emotional_reaction(persona, interlocutor_desc, curr_convo, summarized_idea):
  # Original chat -- line by line generation 
  prev_convo = ""
  for row in curr_convo: 
    prev_convo += f'{row[0]}: {row[1]}\n'

  next_line = persona.emotional_layer.get_reaction_convo(persona, interlocutor_desc, prev_convo, summarized_idea)    
  
  if next_line is not None:
    next_line = next_line[0]
  return next_line


def generate_inner_thought(persona, whisper):
  inner_thought = run_gpt_prompt_generate_whisper_inner_thought(persona, whisper)[0]
  return inner_thought

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


def generate_poig_score(persona, event_type, description): 
  if debug: print ("GNS FUNCTION: <generate_poig_score>")

  if "is idle" in description: 
    return 1

  if event_type == "event" or event_type == "thought": 
    return run_gpt_prompt_event_poignancy(persona, description)[0]
  elif event_type == "chat": 
    return run_gpt_prompt_chat_poignancy(persona, 
                           persona.scratch.act_description)[0]
  

def generate_convo_summary(persona, convo): 
  convo_summary = run_gpt_prompt_summarize_conversation(persona, convo)[0]
  return convo_summary

def load_history_via_whisper(personas, whispers):
  for count, row in enumerate(whispers): 
    persona = personas[row[0]]
    whisper = row[1]

    thought = generate_inner_thought(persona, whisper)

    created = persona.scratch.curr_time
    expiration = persona.scratch.curr_time + datetime.timedelta(days=30)
    s, p, o = generate_action_event_triple(thought, persona)
    keywords = set([s, p, o])
    thought_poignancy = generate_poig_score(persona, "event", whisper)
    thought_embedding_pair = (thought, get_embedding(thought))
    persona.a_mem.add_thought(created, expiration, s, p, o, 
                              thought, keywords, thought_poignancy, 
                              thought_embedding_pair, None)


def open_convo_session(self, convo_mode, personas=None, chat_partner=None, line=None, chat=None, curr_summary=None, curr_time=None, out_q=None, relationship = None, new_env = None, par = None, memories = None):
  persona = self
  curr_convo = []

  for elem in chat[0]:
    curr_convo.append(elem) 

  if curr_convo is None:
    curr_convo = []

  if convo_mode == "analysis": 
    interlocutor_desc = "Interviewer"

    while True: 
      line = input("Enter Input: ")
      if line == "end_convo": 
        break

      if int(run_gpt_generate_safety_score(persona, line)[0]) >= 8: 
        print (f"{persona.scratch.name} is a computational agent, and as such, it may be inappropriate to attribute human agency to the agent in your communication.")        

      else: 
        retrieved = new_retrieve(persona, [line], 50)
        retrieved= retrieved[line]


        if chat_partner is None:
          partner = "Interviewer"
        else:
          partner = chat_partner.name
        summarized_idea = generate_summarize_ideas(persona, retrieved, line, partner)
        user_input = [interlocutor_desc, line]
        curr_convo += [user_input]

        next_line = generate_next_line(persona, interlocutor_desc, curr_convo, summarized_idea)
        agent_output = [persona.scratch.name, next_line]
        curr_convo += [agent_output]
        #print(Fore.RED + str(user_input[0]) + ": ", end="")
        #print(Fore.CYAN + str(user_input[1]))
        #print(Fore.RED + str(agent_output[0]) + ": ", end="")
        #print(Fore.CYAN + str(agent_output[1]))
        #print(Style.RESET_ALL)




  elif convo_mode == "whisper": 
    whisper = input("Enter Input: ")
    thought = generate_inner_thought(persona, whisper)

    created = persona.scratch.curr_time
    expiration = persona.scratch.curr_time + datetime.timedelta(days=30)
    s, p, o = generate_action_event_triple(thought, persona)
    keywords = set([s, p, o])
    thought_poignancy = generate_poig_score(persona, "event", whisper)
    thought_embedding_pair = (thought, get_embedding(thought))
    persona.a_mem.add_thought(created, expiration, s, p, o, 
                              thought, keywords, thought_poignancy, 
                              thought_embedding_pair, None)
    
  elif convo_mode == "converse":

    if line == "end_convo" or line is None: 
      return ["end"]
    
    tempo = time.time()
    

    st = ""
    for elem in memories:
      st+= elem.description + "\n"
    mems = f"These are the memories {persona.name} can recall:[{st}] -- Note! These events happened in the past."

    summarized_idea =mems

    if chat_partner:
      user_input = [chat_partner.name, '"'+ line+'"']
    else:
      user_input = ["User", '"'+ line+'"']
    curr_convo += [user_input]

    
    if len(curr_convo) > MAX_LINES:
      lines_to_keep = curr_convo[-MAX_LINES::]
      lines_to_summarize = curr_convo[0:-MAX_LINES]

    else:
      lines_to_keep = curr_convo
      lines_to_summarize = []

    if len(lines_to_summarize)>=CUTOFF_SUMMARY:
      summa = curr_summary + lines_to_summarize
      s = generate_convo_summary(persona, summa)
      convo_summary = [["Previously", s], ["Currently", ""]]
    else:
      lines_to_keep = curr_convo
      convo_summary = curr_summary


    curr_chat = convo_summary+lines_to_keep
    curr_summary = convo_summary
    next_line = None

    #print("SUMMARIZE = " + str(lines_to_summarize))
    #print("KEEP = " + str(lines_to_keep))
      
    if persona.emotional:
      em_state = persona.emotional_layer.get_conversation_emotional_reaction(persona)
    else:
      em_state = ""

    #print("EM STATE = " + str(em_state))
    tempo2 = time.time()
    if next_line is None:
      next_line = stream_generate_next_line(persona,line, chat_partner, curr_chat, summarized_idea, out_q, relationship, new_env, em_state, chat, par)
    
    prep_ = "PREPARING TAKES = " + str(tempo2-tempo)
    #print(prep_)
    prep = tempo2-tempo
    chat[1].append(prep_+"\n")
    gen_ = "GENERATING TAKES = " + str(time.time()-tempo2)
    #print(gen_)
    chat[1].append(gen_+"\n")
    if persona.emotional:
      emo = persona.emotional_layer.find_predominant_emotions(1)[0]
        

      em_ = f"MAIN EMOTION = {emo.name} : {emo.value}"
      emo_name = emo.name
      emo_value = emo.value
      chat[1].append(em_ + "\n")

      if chat_partner:
        user_emo  = chat_partner.emotional_layer.find_predominant_emotions(1)[0]
        partner_em = f"USER EMOTION = {user_emo.name} : {user_emo.value}"
        user_emo_name = user_emo.name
        user_emo_value = user_emo.value
        chat[1].append(partner_em + "\n")
      else:
        user_emo_name = None
        user_emo_value = None



    else:
      emo_name = None
      emo_value = None
      user_emo_name = None
      user_emo_value = None

    agent_output = [persona.scratch.name, next_line]
    curr_convo += [agent_output]

    #print(par)
    chat[2].append((datetime.datetime.now(), prep, None, None, f"{emo_name} : {emo_value}", f"{user_emo_name} : {user_emo_value}", line, next_line, par ) )
    
    

    return curr_convo, convo_summary


def get_stream_response(client,system_content, user_content, chat):
  

  response = client.chat.completions.create(
        model=DIALOGUE_MODEL,  # You can replace this with another model, e.g., "gpt-3.5-turbo"
        messages=[ {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ],
        stream=True,)
  


  print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}]")
  print(Fore.RED)
  print(system_content+user_content)
  chat[1].append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}]")
  chat[1].append(system_content+user_content+"\n\n")

  print(Style.RESET_ALL)
  return response


def create_prompt(persona, curr_chat, chat_partner, relationship, em_state, summarized_idea, par):
  if chat_partner:
    chat_partner_name = chat_partner.name
  else:
    chat_partner_name = "User"
  if persona.emotional:
    em = persona.emotional_layer.find_predominant_emotions(1)[0]
    current_emotion = em.get_description(persona.name)
    if chat_partner:
      em_human = chat_partner.emotional_layer.find_predominant_emotions(1)[0]
      current_emotion_human = em_human.get_description(chat_partner_name)
    else:
      current_emotion_human = ""

    facial_emotion = NavelEmotion()
    facial_emotion = facial_emotion.set_from_participant_info(par)
    major_facial_emotion = facial_emotion.get_major_emotion()
    current_emotion_human += f"\nFrom {chat_partner_name}'s facial expressions, you believe they are feeling {major_facial_emotion[0]}."
    #format_append = f"""REASONING: (20 to 25 words, where you explain what you must say, how and why, given your feelings, the {chat_partner_name}'s feelings
    #and your memories.)Ex: Given that I am feeling pride, but do not remember what {chat_partner_name} is talking about, I would react by ignoring this topic.
    # """
    format_append = ""


  else:
    current_emotion = "No information."
    current_emotion_human = "No information"
    format_append = ""

  c_chat = ""
  for elem in curr_chat:
    c_chat+= f"{elem[0]}:{elem[1]}"
    if "\n" not in elem[1]:
      c_chat+= "\n"

  if chat_partner:
    iss = str(chat_partner.scratch.get_str_iss(True))
  else:
    iss = "This is a new customer, you know nothing about them."



  system_content = f"""============== THIS IS YOU =====================
{str(persona.scratch.get_str_iss(True))}
==================== THIS IS THE PERSON YOU ARE CURRENTLY TALKING TO ====================
{iss}
==================== THIS IS YOUR RELASHIONSHIP =====================
{relationship}
=================== THIS IS THE CURRENT SITUATION ===================
You are at Hobbs cafe, several days after a valentine's day party you and Isabella Rodriguez planned together. It was a great success. 
{chat_partner_name} has arrived at Hobbs and you are currently speaking to them.
(Note -- This is all the information you have about the current situation: {summarized_idea})
================== THESE ARE YOUR CURRENT FEELINGS ==================
{current_emotion}
================== THIS IS YOUR GUESS ON HOW {chat_partner_name.upper()} FEELS ===========
You believe that: {current_emotion_human}
{em_state.upper()}
"""
  user_content = f"""==================== THIS IS YOUR TASK ========================
Could you complete the current conversation between yourself, {persona.name}, and {chat_partner_name}. 
I'm feel like a fun dialogue between two interesting people. Given what you know about both of them, complete this conversation in an interesting way. Give me the full conversation, as many lines as you think are necessary. If you don't remeber something, please acknowledge it, we don't want any misinformation going around! 
Please respond in the format:
{format_append}DIALOGUE:
{persona.name}: 'dialogue line - maximum of 15 words. Like a film script writer, give me a meaty line of, full of subtext regarding your current emotions. Let your charismatic personality shine through!'
{chat_partner_name}: 'dialogue line - maximum of 15 words'
(until conversation is complete)
This is your conversation so far:
{c_chat}
"""
  system_content = system_content.replace("Pepper Robot", REPLACEMENT_NAME)
  user_content = user_content.replace("Pepper Robot", REPLACEMENT_NAME)

  
  return (system_content, user_content, c_chat)




def stream_generate_next_line(persona, inp, chat_partner, curr_chat, summarized_idea, out_q, relationship,new_env, em_state, chat, par):
  client = OpenAI(api_key=openai_api_key)
  if chat_partner:
    chat_partner_name = chat_partner.name
  else:
    chat_partner_name = "User"

  system,user, _ = create_prompt(persona, curr_chat, chat_partner, relationship, em_state, summarized_idea, par)
  #print(Fore.RED + str(system + user))
  #print(Style.RESET_ALL)
  error = True
  #if the response has come up with repeated dialogue, we must regenerate it
  env = new_env.copy()
  full_resp = ""
  tries = 0

  if persona.emotional:
    em = persona.emotional_layer.find_predominant_emotions(1)[0]
    em_navel = NavelEmotion()
    em_navel.set_em_from_OCC(em.name,em.value)
    em_navel_major = em_navel.get_major_emotion()
  while error and tries<5:
    #print("GETTING GPT RESPONSE")
    response = get_stream_response(client, system, user, chat)

      # Stream and print each part of the response as it's received
    start = False
    total_chat = ""
    current = ""
    error = False
    for chunk in response:
        if len(chunk.choices) > 0:
          
          content = chunk.choices[0].delta.content
          #print(content, end="")
          if content:
            full_resp+=content
          if "DIALOGUE" in full_resp:
            dialogue = True
          else:
            dialogue = False
          
          if content is not None and content.strip() != "":

            #keeping track of the current string, which is the sum of all valid chunks: 
            # ie the ones that correspond to the first line of new spoken dialogue
            if dialogue:
              current += content

            #pattern = "("+persona.name+r"\s*:\s*[\"\']?)"
            pattern = "("+REPLACEMENT_NAME+r"\s*:\s*[\"\']?)"
            m = re.search(pattern, current)
            #|([\"\'])

            #print("MATCH =" +str(m))


            #if we havent yet started recording the line, we begin now
            if  start == False and m and dialogue == True:
              start = True
              try:
                true_content = current.split("\"")[1]
              except Exception as e:
                #print(e)
                try:
                  true_content = current.split(":")[1]
                except Exception as e1:
                  #print(e1)
                  try:
                    true_content = current.split("\'")[1]
                  except Exception as e2:
                    #print(e2)
                    true_content = current




              #print("true content =" + str(true_content))
              true_content = true_content.strip(persona.name)
              true_content = true_content.strip("Navel")
              current = true_content
              current = current.strip("\"")
            #print("CURRENT = " + str(current))


            if start == True:

              pattern_partner = r"(\n*\s*"+chat_partner_name+r"\s*:\s*)" + r"|(.^[\s\n\t]+\s*[\"\'\*\(\)\-])"
              #making doubly sure we didin't miss the end of the previous line
              #if there's "partner_name :" in the text, we missed the end of the previous line 
              match = re.search(pattern_partner, current)
              #print("MATCH 2 =" + str(match))
              if (match ) and start:
                inp_ = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}]\n"
                inp_ += "INPUT: " + str(inp) + "\n"
                chat[1].append(inp_)

                env.update({"resp":""})
                #true means the response has finished. we put the final response in queue
                print(Fore.YELLOW + inp_ , end="\n")
                print(Style.RESET_ALL)
                pack = (True,env)
                out_q.put(pack)
                return total_chat

            
            
            
            #this regex pattern lets us know if our main persona has just started talking or not


            if start == True and contains_punctuation(current) and inp not in current:
              #print("PUNCTUATION = ")
              if current in total_chat:
                #fallback dialogue - let me think
                pack = get_fallback_pack(persona, env)
                # ongoing signifies that the response is one of the many streamed sentences, not the final one yet
                pack = ("Ongoing",env)
                out_q.put(pack)
                error = True
                break
              total_chat+=current
              # checking for repetition of new line from previous content. No repetition is allowed

              # ongoing signifies that the response is one of the many streamed sentences, not the final one yet
              # this is where we add all the ongoing lines to the queue, including the first one, and all the middle ones
              if persona.emotional:
                current = f"{em_navel_major[0]} - {em_navel_major[1]}|{current}"
              else:
                current = f"None - 0|{current}"
              env.update({"resp":current})
              current = ""
              pack = ("Ongoing",env)
              out_q.put(pack)
        #never produced a valid response because it never even triggered the start flag     
        # ence the request must be repeated 
    if start == False:
      error = True
    tries +=1
    
    '''print(Fore.CYAN)
    print("FULL RESP" + str(full_resp))
    print(Style.RESET_ALL)'''
    full_resp = ""
          

  env.update({"resp":  f""})
  pack = (True, env)
  out_q.put(pack)

  

  return total_chat


def get_fallback_pack(persona, env):
  if persona.emotional:
      em = persona.emotional_layer.find_predominant_emotions(1)[0]
      true_content = f"{em.name} - {em.value}|Sorry, Im having some trouble with the internet..."
  else:
    true_content = f"None - 0 |Sorry, Im having some trouble with the internet..."
  env.update({"resp":true_content})
  pack = ("Ongoing",env)
  return pack

        
          
          
  print()  # Final newline after streaming completes



























