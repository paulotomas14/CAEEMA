"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: reverie.py
Description: This is the main program for running generative agent simulations
that defines the ReverieServer class. This class maintains and records all  
states related to the simulation. The primary mode of interaction for those  
running the simulation should be through the open_server function, which  
enables the simulator to input command-line prompts for running and saving  
the simulation, among other tasks.

Release note (June 14, 2023) -- Reverie implements the core simulation 
mechanism described in my paper entitled "Generative Agents: Interactive 
Simulacra of Human Behavior." If you are reading through these lines after 
having read the paper, you might notice that I use older terms to describe 
generative agents and their cognitive modules here. Most notably, I use the 
term "personas" to refer to generative agents, "associative memory" to refer 
to the memory stream, and "reverie" to refer to the overarching simulation 
framework.
"""
import traceback
import sys
sys.path.append('')

import os



#sys.path.append(str(os.path.dirname(os.path.abspath(__file__)))+ "/../..")
##print(sys.path)

import json
import numpy
import datetime
import pickle
import time
from datetime import timedelta
import math
import os
import shutil
import traceback
from pathlib import Path
from environment.frontend_server.robot import interview
from multiprocessing import Process, Queue, Manager


from selenium import webdriver

from global_methods import *
from utils import *
from maze import *
from persona.persona import *
from persona.cognitive_modules.variables import verbose_movements, ExperimentData


from colorama import Fore, Style
import os

##############################################################################
#                                  REVERIE                                   #
##############################################################################



class ReverieServer: 
  def __init__(self, 
               fork_sim_code,
               sim_code, emotional):
    # FORKING FROM A PRIOR SIMULATION:
    # <fork_sim_code> indicates the simulation we are forking from. 
    # Interestingly, all simulations must be forked from some initial 
    # simulation, where the first simulation is "hand-crafted".
    os.environ["OPENAI_API_KEY"] = openai_api_key
    self.fork_sim_code = fork_sim_code
    fork_folder = f"{fs_storage}/{self.fork_sim_code}"

    # <sim_code> indicates our current simulation. The first step here is to 
    # copy everything that's in <fork_sim_code>, but edit its 
    # reverie/meta/json's fork variable. 
    self.sim_code = sim_code
    sim_folder = f"{fs_storage}/{self.sim_code}"
   
    copyanything(fork_folder, sim_folder)

    with open(f"{sim_folder}/reverie/meta.json") as json_file:  
      reverie_meta = json.load(json_file)

    with open(f"{sim_folder}/reverie/meta.json", "w") as outfile: 
      reverie_meta["fork_sim_code"] = fork_sim_code
      outfile.write(json.dumps(reverie_meta, indent=2))

    # LOADING REVERIE'S GLOBAL VARIABLES
    # The start datetime of the Reverie: 
    # <start_datetime> is the datetime instance for the start datetime of 
    # the Reverie instance. Once it is set, this is not really meant to 
    # change. It takes a string date in the following example form: 
    # "June 25, 2022"
    # e.g., ...strptime(June 25, 2022, "%B %d, %Y")
    self.start_time = datetime.datetime.strptime(
                        f"{reverie_meta['start_date']}, 00:00:00",  
                        "%B %d, %Y, %H:%M:%S")
    # <curr_time> is the datetime instance that indicates the game's current
    # time. This gets incremented by <sec_per_step> amount everytime the world
    # progresses (that is, everytime curr_env_file is recieved). 
    self.curr_time = datetime.datetime.strptime(reverie_meta['curr_time'], 
                                                "%B %d, %Y, %H:%M:%S")
    # <sec_per_step> denotes the number of seconds in game time that each 
    # step moves foward. 
    self.sec_per_step = SECS_PER_STEP
    #reverie_meta['sec_per_step']
    
    # <maze> is the main Maze instance. Note that we pass in the maze_name
    # (e.g., "double_studio") to instantiate Maze. 
    # e.g., Maze("double_studio")
    self.maze = Maze(reverie_meta['maze_name'])
    
    # <step> denotes the number of steps that our game has taken. A step here
    # literally translates to the number of moves our personas made in terms
    # of the number of tiles. 
    self.step = reverie_meta['step']

    # SETTING UP PERSONAS IN REVERIE
    # <personas> is a dictionary that takes the persona's full name as its 
    # keys, and the actual persona instance as its values.
    # This dictionary is meant to keep track of all personas who are part of
    # the Reverie instance. 
    # e.g., ["Isabella Rodriguez"] = Persona("Isabella Rodriguezs")
    self.personas = dict()
    # <personas_tile> is a dictionary that contains the tile location of
    # the personas (!-> NOT px tile, but the actual tile coordinate).
    # The tile take the form of a set, (row, col). 
    # e.g., ["Isabella Rodriguez"] = (58, 39)
    self.personas_tile = dict()
    
    # # <persona_convo_match> is a dictionary that describes which of the two
    # # personas are talking to each other. It takes a key of a persona's full
    # # name, and value of another persona's full name who is talking to the 
    # # original persona. 
    # # e.g., dict["Isabella Rodriguez"] = ["Maria Lopez"]
    # self.persona_convo_match = dict()
    # # <persona_convo> contains the actual content of the conversations. It
    # # takes as keys, a pair of persona names, and val of a string convo. 
    # # Note that the key pairs are *ordered alphabetically*. 
    # # e.g., dict[("Adam Abraham", "Zane Xu")] = "Adam: baba \n Zane:..."
    # self.persona_convo = dict()
    #print(reverie_meta)
    # Loading in all personas. 
    init_env_file = f"{sim_folder}/environment/{str(self.step)}.json"
    init_env = json.load(open(init_env_file))

    wrong_inp = True
    change = False
    while wrong_inp:
      inp = input("Do you wanna reset any agent?[y/n]: ")
      if inp == 'y' or inp == 'n':
        if inp == 'y':
          change = True

        wrong_inp=False

    for persona_name in reverie_meta['persona_names']: 
      persona_folder = f"{sim_folder}/personas/{persona_name}"
      p_x = init_env[persona_name]["x"]
      p_y = init_env[persona_name]["y"]

      new = False
      if change:
        wrong_inp = True
        while wrong_inp:
          inp = input(f"Do you wanna reset {persona_name}?[y/n]: ")
          if inp == 'y' or inp == 'n':
            if inp == 'y':
              new = True
            wrong_inp=False



      curr_persona = Persona(persona_name, self.curr_time, persona_folder, emotional, new)

      self.personas[persona_name] = curr_persona
      self.personas_tile[persona_name] = (p_x, p_y)
      self.maze.tiles[p_y][p_x]["events"].add(curr_persona.scratch
                                              .get_curr_event_and_desc())

    # REVERIE SETTINGS PARAMETERS:  
    # <server_sleep> denotes the amount of time that our while loop rests each
    # cycle; this is to not kill our machine. 
    self.server_sleep = 0.3

    # SIGNALING THE FRONTEND SERVER: 
    # curr_sim_code.json contains the current simulation code, and
    # curr_step.json contains the current step of the simulation. These are 
    # used to communicate the code and step information to the frontend. 
    # Note that step file is removed as soon as the frontend opens up the 
    # simulation. 
    curr_sim_code = dict()
    curr_sim_code["sim_code"] = self.sim_code
    with open(f"{fs_temp_storage}/curr_sim_code.json", "w") as outfile: 
      outfile.write(json.dumps(curr_sim_code, indent=2))
    
    curr_step = dict()
    curr_step["step"] = self.step
    with open(f"{fs_temp_storage}/curr_step.json", "w") as outfile: 
      outfile.write(json.dumps(curr_step, indent=2))


  def save(self, t): 
    """
    Save all Reverie progress -- this includes Reverie's global state as well
    as all the personas.  

    INPUT
      None
    OUTPUT 
      None
      * Saves all relevant data to the designated memory directory
    """
    # <sim_folder> points to the current simulation folder.
    print("SAVING SERVER")
    sim_folder = f"{fs_storage}/{self.sim_code}"

    # Save Reverie meta information.
    reverie_meta = dict() 
    reverie_meta["fork_sim_code"] = self.fork_sim_code
    reverie_meta["start_date"] = self.start_time.strftime("%B %d, %Y")
    reverie_meta["curr_time"] = self.curr_time.strftime("%B %d, %Y, %H:%M:%S")
    reverie_meta["sec_per_step"] = self.sec_per_step
    reverie_meta["maze_name"] = self.maze.maze_name
    reverie_meta["persona_names"] = list(self.personas.keys())
    reverie_meta["step"] = self.step
    reverie_meta["full_time"] = time.time() -t
    reverie_meta_f = f"{sim_folder}/reverie/meta.json"
    with open(reverie_meta_f, "w") as outfile: 
      outfile.write(json.dumps(reverie_meta, indent=2))

    # Save the personas.
    for persona_name, persona in self.personas.items(): 
      #print("SAVING PERSONAS")
      save_folder = f"{sim_folder}/personas/{persona_name}/bootstrap_memory"
      persona.save(save_folder)


  def start_path_tester_server(self): 
    """
    Starts the path tester server. This is for generating the spatial memory
    that we need for bootstrapping a persona's state. 

    To use this, you need to open server and enter the path tester mode, and
    open the front-end side of the browser. 

    INPUT 
      None
    OUTPUT 
      None
      * Saves the spatial memory of the test agent to the path_tester_env.json
        of the temp storage. 
    """
    def print_tree(tree): 
      def _print_tree(tree, depth):
        dash = " >" * depth

        if type(tree) == type(list()): 
          if tree:
            print (dash, tree)
          return 

        for key, val in tree.items(): 
          if key: 
            print (dash, key)
          _print_tree(val, depth+1)
      
      _#print_tree(tree, 0)

    # <curr_vision> is the vision radius of the test agent. Recommend 8 as 
    # our default. 
    curr_vision = 8
    # <s_mem> is our test spatial memory. 
    s_mem = dict()

    # The main while loop for the test agent. 
    while (True): 
      try: 
        curr_dict = {}
        tester_file = fs_temp_storage + "/path_tester_env.json"
        if check_if_file_exists(tester_file): 
          with open(tester_file) as json_file: 
            curr_dict = json.load(json_file)
            os.remove(tester_file)
          
          # Current camera location
          curr_sts = self.maze.sq_tile_size
          curr_camera = (int(math.ceil(curr_dict["x"]/curr_sts)), 
                         int(math.ceil(curr_dict["y"]/curr_sts))+1)
          curr_tile_det = self.maze.access_tile(curr_camera)

          # Initiating the s_mem
          world = curr_tile_det["world"]
          if curr_tile_det["world"] not in s_mem: 
            s_mem[world] = dict()

          # Iterating throughn the nearby tiles.
          nearby_tiles = self.maze.get_nearby_tiles(curr_camera, curr_vision)
          for i in nearby_tiles: 
            i_det = self.maze.access_tile(i)
            if (curr_tile_det["sector"] == i_det["sector"] 
                and curr_tile_det["arena"] == i_det["arena"]): 
              if i_det["sector"] != "": 
                if i_det["sector"] not in s_mem[world]: 
                  s_mem[world][i_det["sector"]] = dict()
              if i_det["arena"] != "": 
                if i_det["arena"] not in s_mem[world][i_det["sector"]]: 
                  s_mem[world][i_det["sector"]][i_det["arena"]] = list()
              if i_det["game_object"] != "": 
                if (i_det["game_object"] 
                    not in s_mem[world][i_det["sector"]][i_det["arena"]]):
                  s_mem[world][i_det["sector"]][i_det["arena"]] += [
                                                         i_det["game_object"]]

        # Incrementally outputting the s_mem and saving the json file. 
        #print ("= " * 15)
        out_file = fs_temp_storage + "/path_tester_out.json"
        with open(out_file, "w") as outfile: 
          outfile.write(json.dumps(s_mem, indent=2))
        #print_tree(s_mem)

      except:
        pass

      time.sleep(self.server_sleep * 10)


  def start_server(self, int_counter, t): 
    """
    The main backend server of Reverie. 
    This function retrieves the environment file from the frontend to 
    understand the state of the world, calls on each personas to make 
    decisions based on the world state, and saves their moves at certain step
    intervals. 
    INPUT
      int_counter: Integer value for the number of steps left for us to take
                   in this iteration. 
    OUTPUT 
      None
    """
    # <sim_folder> points to the current simulation folder.
    sim_folder = f"{fs_storage}/{self.sim_code}"

    # When a persona arrives at a game object, we give a unique event
    # to that object. 
    # e.g., ('double studio[...]:bed', 'is', 'unmade', 'unmade')
    # Later on, before this cycle ends, we need to return that to its 
    # initial state, like this: 
    # e.g., ('double studio[...]:bed', None, None, None)
    # So we need to keep track of which event we added. 
    # <game_obj_cleanup> is used for that. 
    game_obj_cleanup = dict()

    # The main while loop of Reverie. 
    while (True): 
      # Done with this iteration if <int_counter> reaches 0. 
      ##print(int_counter)
      if int_counter == 0: 
        break

      # <curr_env_file> file is the file that our frontend outputs. When the
      # frontend has done its job and moved the personas, then it will put a 
      # new environment file that matches our step count. That's when we run 
      # the content of this for loop. Otherwise, we just wait. 
      curr_env_file = f"{sim_folder}/environment/{self.step}.json"
      #print(curr_env_file)
      if check_if_file_exists(curr_env_file):
        # If we have an environment file, it means we have a new perception
        # input to our personas. So we first retrieve it.
        try: 
          # Try and save block for robustness of the while loop.
          with open(curr_env_file) as json_file:
            new_env = json.load(json_file)
            env_retrieved = True
        except: 
          pass
      
        if env_retrieved: 
          # This is where we go through <game_obj_cleanup> to clean up all 
          # object actions that were used in this cylce. 
          for key, val in game_obj_cleanup.items(): 
            # We turn all object actions to their blank form (with None). 
            self.maze.turn_event_from_tile_idle(key, val)
          # Then we initialize game_obj_cleanup for this cycle. 
          game_obj_cleanup = dict()

          # We first move our personas in the backend environment to match 
          # the frontend environment. 
          for persona_name, persona in self.personas.items(): 
            # <curr_tile> is the tile that the persona was at previously. 
            curr_tile = self.personas_tile[persona_name]
            # <new_tile> is the tile that the persona will move to right now,
            # during this cycle. 
            new_tile = (new_env[persona_name]["x"], 
                        new_env[persona_name]["y"])

            # We actually move the persona on the backend tile map here. 
            self.personas_tile[persona_name] = new_tile
            self.maze.remove_subject_events_from_tile(persona.name, curr_tile)
            self.maze.add_event_from_tile(persona.scratch
                                         .get_curr_event_and_desc(), new_tile)

            # Now, the persona will travel to get to their destination. *Once*
            # the persona gets there, we activate the object action.
            if not persona.scratch.planned_path: 
              # We add that new object action event to the backend tile map. 
              # At its creation, it is stored in the persona's backend. 
              game_obj_cleanup[persona.scratch
                               .get_curr_obj_event_and_desc()] = new_tile
              self.maze.add_event_from_tile(persona.scratch
                                     .get_curr_obj_event_and_desc(), new_tile)
              # We also need to remove the temporary blank action for the 
              # object that is currently taking the action. 
              blank = (persona.scratch.get_curr_obj_event_and_desc()[0], 
                       None, None, None)
              self.maze.remove_event_from_tile(blank, new_tile)

          # Then we need to actually have each of the personas perceive and
          # move. The movement for each of the personas comes in the form of
          # x y coordinates where the persona will move towards. e.g., (50, 34)
          # This is where the core brains of the personas are invoked. 
          movements = {"persona": dict(), 
                       "meta": dict()}
          for persona_name, persona in self.personas.items(): 
            # <next_tile> is a x,y coordinate. e.g., (58, 9)
            # <pronunciatio> is an emoji. e.g., "\ud83d\udca4"
            # <description> is a string description of the movement. e.g., 
            #   writing her next novel (editing her novel) 
            #   @ double studio:double studio:common room:sofa
            next_tile, pronunciatio, description = persona.move(
              self.maze, self.personas, self.personas_tile[persona_name], 
              self.curr_time)
            movements["persona"][persona_name] = {}
            movements["persona"][persona_name]["movement"] = next_tile
            movements["persona"][persona_name]["pronunciatio"] = pronunciatio
            movements["persona"][persona_name]["description"] = description
            movements["persona"][persona_name]["chat"] = (persona
                                                          .scratch.chat)
            if persona.emotional:
              movements['persona'][persona_name]['emotion'] = persona.emotional_layer.find_predominant_emotions(1)[0].get_description(persona.name)
            else:
              movements['persona'][persona_name]['emotion'] = None


            if verbose_movements:
              print(Fore.LIGHTRED_EX + str(persona_name) + "(" + str(self.step)+") : ") 
              print(Fore.CYAN + "\t ->" + str(movements["persona"][persona_name]))
              print("Persona time = " + str(persona.scratch.curr_time))
              print(Style.RESET_ALL)

          # Include the meta information about the current stage in the 
          # movements dictionary. 
          movements["meta"]["curr_time"] = (self.curr_time 
                                             .strftime("%B %d, %Y, %H:%M:%S"))

          # We then write the personas' movements to a file that will be sent 
          # to the frontend server. 
          # Example json output: 
          # {"persona": {"Maria Lopez": {"movement": [58, 9]}},
          #  "persona": {"Klaus Mueller": {"movement": [38, 12]}}, 
          #  "meta": {curr_time: <datetime>}}
          curr_move_file = Path(f"{sim_folder}/movement/{self.step}.json")
          curr_move_file.parent.mkdir(exist_ok=True, parents=True)
          with open(curr_move_file, "w") as outfile: 
            outfile.write(json.dumps(movements, indent=2))

          # After this cycle, the world takes one step forward, and the 
          # current time moves by <sec_per_step> amount. 
          self.step += 1
          self.curr_time += datetime.timedelta(seconds=self.sec_per_step)
          '''for persona_name, persona in self.personas.items(): 
            persona.scratch.curr_time = self.curr_time'''
          if self.step%10 == 0:

            self.save(t)


          int_counter -= 1
      else:
        print("FILE DOES NOT EXIST")    
      # Sleep so we don't burn our machines.
      curr_step = dict()
      curr_step["step"] = self.step -1
      with open(f"{fs_temp_storage}/curr_step.json", "w") as outfile: 
        outfile.write(json.dumps(curr_step, indent=2))
      time.sleep(self.server_sleep)
      
      #print("BEGIN NEXT STEP")

  def new_step_language_agent(self, procs,i, out_q, persona, human_persona, chat, curr_summary, new_env, sim_folder, relationship = None, par = None, memories=None):
    t = time.time()
    inp = new_env["input"]
    _, curr_summary = persona.open_convo_session("converse", self.personas, human_persona, inp, chat, curr_summary, persona.scratch.curr_time, out_q, relationship,new_env, par, memories)
    
    
    for p in procs:
      if p==i:
        ind = procs.index(p)
        try:
          procs.pop(ind)
        except Exception as e:
          print("COULD NOT POP PROCESS AFTER COMPLETING REQUEST: " + str(e))


    

    
  def load_new_env(self, q):
    env_retrieved = False
    
    while env_retrieved == False:
      try:
        new_env = q.get()
        env_retrieved = True
      except Exception as e:
        print("COULD NOT READ INPUT QUEUE: " + str(e))
      
    return new_env
  

  def get_chatting_event_quad(self, speaker, line, persona_name, human_name):
    subject = speaker
    if speaker == persona_name:
      obj = human_name
    else:
      obj = persona_name
    event = (subject, ' chatting with ', obj, f'{subject} said: "{line}" to {obj}')

    return event

  def get_events_for_real_time_interaction(self, chat, persona, persona_name, human_name, nodes, inp):
    new, ongoing, finished = [], [], []
            
    for j in range(max(len(chat[0])-int(persona.scratch.retention/2), 0), len(chat[0])):
      event = self.get_chatting_event_quad(chat[0][j][0], chat[0][j][1], persona_name, human_name)
      ongoing.append(event)
      
    for j in range(max(len(nodes)-int(persona.scratch.retention*2), 0), len(nodes)):
      mem = nodes[j][1]
      quad = (mem.subject, mem.predicate, mem.object, mem.description)
      finished.append(quad)
    
    new_event = self.get_chatting_event_quad(human_name, inp, persona_name, human_name)
    new.append(new_event)

    event_triplet = new, ongoing, finished
    return event_triplet
  

  def start_full_architecture_convo(self): 
    """
    The main backend server of Reverie. 
    This function retrieves the environment file from the frontend to 
    understand the state of the world, calls on each personas to make 
    decisions based on the world state, and saves their moves at certain step
    intervals. 
    INPUT
      int_counter: Integer value for the number of steps left for us to take
                   in this iteration. 
    OUTPUT 
      None
    """
    # <sim_folder> points to the current simulation folder.
    manager = Manager()
    procs = manager.list()
    chat = manager.list()
    chat.append(manager.list())
    chat.append(manager.list())
    chat.append(manager.list())

    appraisals = manager.list()
    appraisals_human = manager.list()

    all_procs = []
    appraisal_procs = []
    sim_folder = f"{fs_storage}/{self.sim_code}"

    # The main while loop of Reverie. 
    self.curr_time += datetime.timedelta(days=1, hours=1)
    personas_str = [persona_name for persona_name, persona in self.personas.items()]
    choice_human = int(input("Who are you?\nChoose a persona from the available, by index " + str(personas_str)+ ": "))
    choice = int(input("Who are you talking to?\nChoose a persona from the available, by index " + str(personas_str)+ ": "))

    human_name = personas_str[choice_human]
    human_persona = self.personas[human_name]
    persona_name = personas_str[choice]
    persona = self.personas[persona_name]
    old_env = {"input": "Empty"}
    new_env = {"input":""}
    old_p = None
    persona.scratch.curr_time = self.curr_time
    persona.plan_robot(human_persona)
    human_persona.scratch.curr_time = self.curr_time
    if persona.emotional:
      persona.emotional_layer.last_update = self.curr_time
      human_persona.emotional_layer.last_update = self.curr_time
    persona.setup_convo_robot(f"{persona_name} is done with their prior actions, and has begun chatting with {human_name}." , human_name)
    input_queue = Queue()
    output_queue = Queue()
    if persona.emotional:
      persona.emotional_layer.live_constant = LIVE_MODIFYER_FOR_EMOTION 
      #persona.emotional_layer.live_constant = 1

      #persona.emotional_layer.print_layer()



    p = Process(target=interview, args= (persona.emotional, input_queue,  output_queue, human_name, fs_storage, self.sim_code, self.step,chat, persona_name, human_name,))
    all_procs.append((0,p))
    p.start()
    curr_summary = []
    experiment_data = ExperimentData()
    

    focal_points = [f"{human_persona.scratch.name}"]
    retrieved = new_retrieve(persona, focal_points, 50)
    relationship = generate_summarize_agent_relationship(persona, human_persona, retrieved)

    # take this off later
    #chat = [['Klaus Mueller', 'Hello, Maria!'], ['Maria Lopez', 'Hi Klaus! How are you doing today?'], ['Klaus Mueller', "I'm doing okay. How's your streaming going?"], ['Maria Lopez', "My streaming is going well, actually! I've been getting some new followers and some good feedback on my latest gameplay. How about you, Klaus? How's work going for you today?"], ['Klaus Mueller', 'Oh, you know, research is going slow. Kinda annoying me to be honest.'], ['Maria Lopez', 'Oh, I see. Maybe you need a break to clear your mind and get some fresh perspective. Have you taken a moment to step back and reassess your approach to your research?'], ['Klaus Mueller', "Ahahah, yeah, I know I should do that. But it's so difficult to take a step back, you know? You feel guilty for not being productive enough..."], ['Maria Lopez', 'I completely understand that feeling, Klaus. But sometimes taking a break can actually help you be more productive in the long run. Maybe try going for a walk or doing something that relaxes you for a bit. It might give you a fresh perspective on your research.'], ['Klaus Mueller', 'Thanks for the support sweetie, it means a lot! What about you, are classes going well?'], ['Maria Lopez', "Classes are going well for me, thanks for asking! I've been really enjoying my physics lectures and I feel like I'm learning a lot. I'm currently on my way to my physics class, actually. After that, I'm planning to study at the library, do some Twitch streaming, have dinner, and then relax in the evening. It's a busy day but I'm excited for it!"], ['Klaus Mueller', "Ahahah, you're so active! I'm feeling a little bit ashamed now, this young whipper-snapper is showing me up!"], ['Maria Lopez', "I'm glad to hear that you're impressed with my schedule! I really enjoy staying busy and being active. It keeps me motivated and helps me stay on track with my goals. How about you, Klaus? How do you like to stay productive and motivated in your work?"]]
    


    while (True): 
      # Done with this iteration if <int_counter> reaches 0. 

      # <curr_env_file> file is the file that our frontend outputs. When the
      # frontend has done its job and moved the personas, then it will put a 
      # new environment file that matches our step count. That's when we run 
      # the content of this for loop. Otherwise, we just wait. 
      
      env_retrieved = False

      #print("HERE")
      tempo = time.time()
      new_env = self.load_new_env(input_queue)
      #curr_env_file = f"{sim_folder}/environment_robot/{self.step}.json"

      ##print("___" + str(new_env) +" -> " + str(curr_env_file))
      ####print("NEW ENV")
      

      if new_env is not None and new_env["input"]:    
        if new_env["input"] != old_env["input"]:
          env_retrieved = True
      ##print(env_retrieved)
    
      if env_retrieved: 
        inp = new_env["input"]


        if inp == "end_convo":
          break

        if inp != "!!!LISTENING!!!":
          ##print("GOT ON AGENT SIDE =  "+ str(inp))
          participant_info = new_env["participant_info"]

          par = f"Participant Info: {participant_info}"
          chat[1].append(par)
          print(par)
          if "terminate" in inp.lower():
            break
          persona.scratch.curr_time = self.curr_time
          if persona.emotional:
            if appraisals is not None and len(appraisals)>0:
                
                persona.emotional_layer.update( appraisals, self.curr_time, persona)
                persona.emotional_layer.print_layer(chat)
            if appraisals_human is not None and len(appraisals_human)>0:
                  human_persona.emotional_layer.update(appraisals_human, self.curr_time, human_persona)
                  human_persona.emotional_layer.print_layer(chat)

          retrieved_original = new_retrieve(persona, [inp + "\nFeelings."], 10)
          retrieved = retrieved_original[inp + "\nFeelings."]
         

          nodes = [[i.created, i]
                    for i in retrieved]
          nodes = sorted(nodes, key=lambda x: x[0], reverse=True)

          memories = [n[1] for n in nodes]

        # checka se dá pra por retention nos eventos guardados por cada emoção - acho que está
          if persona.emotional:

            retrieved_original_human = new_retrieve(human_persona, [inp + "\nFeelings."], 10)
            retrieved_human = retrieved_original_human[inp + "\nFeelings."]

            nodes_human = [[i.created, i]
                      for i in retrieved_human]
            nodes_human = sorted(nodes_human, key=lambda x: x[0], reverse=True)

            #memories_human = [n[1] for n in nodes_human]
            
            app_len = len(appraisal_procs)
            
            event_triplet = self.get_events_for_real_time_interaction( chat, persona, persona_name, human_name, nodes, inp)
            #print("PERSONA TRIPLET = " + str(event_triplet))
            event_triplet_human = self.get_events_for_real_time_interaction( chat, human_persona, persona_name, human_name, nodes_human, inp)
            #print("HUMAN TRIPLET = "+ str(event_triplet_human))
            p_app = Process(target=persona.emotional_layer.get_appraisals_from_llm, args= (appraisals, event_triplet, persona, self.personas, chat))
            appraisal_procs.append((app_len,p_app))
            p_app.start()

            app_len = len(appraisal_procs)

            p_app_human = Process(target=human_persona.emotional_layer.get_appraisals_from_llm, args= (appraisals_human, event_triplet_human, human_persona, self.personas, chat))
            appraisal_procs.append((app_len,p_app_human))
            p_app_human.start()
            

          i = len(all_procs)
          p_ag = Process(target=self.new_step_language_agent, args= (procs, i, output_queue, persona, human_persona, chat, curr_summary, new_env, sim_folder, relationship, par, memories))
          procs.append(i)
          all_procs.append((i,p_ag))
          p_ag.start()

          old_env=new_env
          # After this cycle, the world takes one step forward, and the 
          # current time moves by <sec_per_step> amount.
        else:
          
          if len(procs):
            try:
              procs, all_procs = self.terminate_procs(procs, all_procs)

            except Exception as e:
              print("Could not close Language Agent process 1: "+ str(e))

        self.step+=1
        self.save_chat(chat, sim_folder, experiment_data)




      delta = time.time()-tempo
      self.curr_time += datetime.timedelta(seconds=delta)
     

    self.join_procs(all_procs)
    self.join_procs(appraisal_procs)

  def save_chat(self, chat, sim_folder, experiment):

    #print("CHAT = " + str(chat))
    reverie_meta_f = f"{sim_folder}/reverie/chat.json"
    with open(reverie_meta_f, "w") as outfile:
      for elem in chat[0]:
        outfile.write(f"[{elem[2]}]\n{elem[0]}:'{elem[1]}'\n")
    reverie_meta_f = f"{sim_folder}/reverie/log.json"
    with open(reverie_meta_f, "w") as outfile:
      for elem in chat[1]:
        outfile.write(f"{elem}\n")
    #experiment.extract_experiment_data(f"{sim_folder}/reverie/log.json")
    for elem in chat[2]:
      experiment.add_entry( elem[0], elem[1], elem[2], elem[3], elem[4], elem[5], elem[6], elem[7], elem[8])
    experiment.save_to_csv(f"{sim_folder}/reverie/experiment_data.csv")
    experiment.save_to_json(f"{sim_folder}/reverie/experiment_data.json")


  def terminate_procs(self, procs, all_procs):
    new_all_procs = []
    for elem in all_procs:
      if elem[0] in procs:
        elem[1].terminate()
        ind = procs.index(elem[0])
        try:
          procs.pop(ind)
        except Exception as e:
          print("COULD NOT POP PROCESS " + str(elem[0])+": " + str(e))
      else:
        new_all_procs = []

    return procs, new_all_procs

        
    return []

  def join_procs(self, procs):
    for elem in procs:
      elem[1].join()

  def summarize_all_memories(self, persona):
    

    memories = persona.a_mem.seq_event + persona.a_mem.seq_thought + persona.a_mem.seq_chat

    nodes = [[i.last_accessed, i]
              for i in memories
              if "idle" not in i.embedding_key]
    nodes = sorted(nodes, key=lambda x: x[0])
    #print(nodes)

    nodes = [node
              for node in nodes
              if  self.curr_time - timedelta(days=2, hours=8)  <  node[0] <= self.curr_time ]
    
    #print(len(nodes))

    split_memories_by_hour = []

    curr_hour = self.curr_time - timedelta(days=2, hours=8)
    nodes = sorted(nodes, key=lambda x: x[0])
    #nodes.reverse()
    index = 0

    while curr_hour < self.curr_time:
      split_memories_by_hour.append((curr_hour, []))
      for node in nodes:
        if curr_hour < node[0] <= curr_hour + timedelta(hours=1):
          split_memories_by_hour[index][1].append(node)

      index += 1
      curr_hour = curr_hour + timedelta(hours=1)

    


    summaries = []
    for elem in split_memories_by_hour:
      print(elem[0], len(elem[1]))
      if len(elem[1])>0:
        sum_prompt = f"This is you: {persona.scratch.get_str_iss(trim=True)}\n\n"

        sum_prompt += f"""These are your memories for this timeframe '{elem[0].strftime("%H:%M")}h':\n"""
        mems = ""
        for mem in elem[1]:
          mems += mem[0].strftime("%H:%M") + f" - {mem[1].description}\n"
        sum_prompt += f"""{mems}

  Please provide a summary of the most significant events, the ones that seem the most impactful, fun and emotional, the ones you would likely reminisce about in the future in bullet points, maximum 3 bullet points
  """
        summary = ChatGPT_single_request(sum_prompt)
      '''else:
        summary = f"{persona.name} slept."'''

      summaries.append((elem[0], summary))

    

    curr_hour = self.curr_time - timedelta(days=2, hours=8)
    
    index = 0
    sums_split_by_day = []

    while curr_hour < self.curr_time:
      sums_split_by_day.append((curr_hour.strftime("%Y-%m-%d %H:%M") + "H", []))
      for sum in summaries:
        if curr_hour < sum[0] <= curr_hour + timedelta(days=1):
          sums_split_by_day[index][1].append(sum)

      index += 1
      curr_hour = curr_hour + timedelta(days=1)

    new_summaries = []
    for elem in sums_split_by_day:
      print(elem[0], len(elem[1]))
      if len(elem[1])>0:
        sum_prompt = f"This is you: {persona.scratch.get_str_iss(trim=True)}\n\n"

        sum_prompt += f"""These are your memories for this timeframe '{elem[0]}':\n"""
        mems = ""
        for mem in elem[1]:
          mems += mem[0].strftime("%H:%M")  + f"H {mem[1]}\n\n"
        sum_prompt += f"""{mems}

  Please provide a summary of the most significant events, the ones that seem the most impactful, fun and emotional, the ones you would likely reminisce about in the future in bullet points, maximum 10 bullet points.
  """
        summary = ChatGPT_single_request(sum_prompt)
        new_summaries.append((elem[0], summary))
      
      for sum in new_summaries:
        print(Fore.GREEN)
        print(sum)
        print(Style.RESET_ALL)

    



    


      

    






    


  def open_server(self): 
    """
    Open up an interactive terminal prompt that lets you run the simulation 
    step by step and probe agent state. 

    INPUT 
      None
    OUTPUT
      None
    """
    #print ("Note: The agents in this simulation package are computational")
    #print ("constructs powered by generative agents architecture and LLM. We")
    #print ("clarify that these agents lack human-like agency, consciousness,")
    #print ("and independent decision-making.\n---")

    # <sim_folder> points to the current simulation folder.
    sim_folder = f"{fs_storage}/{self.sim_code}"
    t = time.time()

    while True: 
      sim_command = input("Enter option: ")
      sim_command = sim_command.strip()
      ret_str = ""

      try: 
        if sim_command.lower() in ["f", "fin", "finish", "save and finish"]: 
          # Finishes the simulation environment and saves the progress. 
          # Example: fin
          self.save(t)
          break

        elif sim_command.lower() == "start path tester mode": 
          # Starts the path tester and removes the currently forked sim files.
          # Note that once you start this mode, you need to exit out of the
          # session and restart in case you want to run something else. 
          shutil.rmtree(sim_folder) 
          self.start_path_tester_server()

        elif sim_command.lower() == "exit":   
          # Finishes the simulation environment but does not save the progress
          # and erases all saved data from current simulation. 
          # Example: exit 
          shutil.rmtree(sim_folder) 
          break 

        elif sim_command.lower() == "save": 
          # Saves the current simulation progress. 
          # Example: save
          self.save(t)

        elif sim_command[:9].lower() == "run robot": 
          # Runs the number of steps specified in the prompt.
          # Example: run 1000
          
          rs.start_full_architecture_convo()

        elif sim_command[:3].lower() == "run": 
          # Runs the number of steps specified in the prompt.
          # Example: run 1000
          int_count = int(sim_command.split()[-1])
          #
          # #print(int_count)
          t = time.time()
          try:
            rs.start_server(int_count, t)
            rs.save(t)

          except Exception as e:
            print("TRACEBACK")
            print(traceback.format_exc())
            print("START SAVE")
            rs.save(t)
            print("END SAVE")
        
          total_time = time.time() -t
          print("Total time = " + str(total_time))

        elif ("#print persona schedule" 
              in sim_command[:22].lower()): 
          # #print the decomposed schedule of the persona specified in the 
          # prompt.
          # Example: #print persona schedule Isabella Rodriguez
          ret_str += (self.personas[" ".join(sim_command.split()[-2:])]
                      .scratch.get_str_daily_schedule_summary())

        elif ("#print all persona schedule" 
              in sim_command[:26].lower()): 
          # #print the decomposed schedule of all personas in the world. 
          # Example: #print all persona schedule
          for persona_name, persona in self.personas.items(): 
            ret_str += f"{persona_name}\n"
            ret_str += f"{persona.scratch.get_str_daily_schedule_summary()}\n"
            ret_str += f"---\n"

        elif ("#print hourly org persona schedule" 
              in sim_command.lower()): 
          # #print the hourly schedule of the persona specified in the prompt.
          # This one shows the original, non-decomposed version of the 
          # schedule.
          # Ex: #print persona schedule Isabella Rodriguez
          ret_str += (self.personas[" ".join(sim_command.split()[-2:])]
                      .scratch.get_str_daily_schedule_hourly_org_summary())

        elif ("#print persona current tile" 
              in sim_command[:26].lower()): 
          # #print the x y tile coordinate of the persona specified in the 
          # prompt. 
          # Ex: #print persona current tile Isabella Rodriguez
          ret_str += str(self.personas[" ".join(sim_command.split()[-2:])]
                      .scratch.curr_tile)

        elif ("#print persona chatting with buffer" 
              in sim_command.lower()): 
          # #print the chatting with buffer of the persona specified in the 
          # prompt.
          # Ex: #print persona chatting with buffer Isabella Rodriguez
          curr_persona = self.personas[" ".join(sim_command.split()[-2:])]
          for p_n, count in curr_persona.scratch.chatting_with_buffer.items(): 
            ret_str += f"{p_n}: {count}"

        elif ("#print persona associative memory (event)" 
              in sim_command.lower()):
          # #print the associative memory (event) of the persona specified in
          # the prompt
          # Ex: #print persona associative memory (event) Isabella Rodriguez
          ret_str += f'{self.personas[" ".join(sim_command.split()[-2:])]}\n'
          ret_str += (self.personas[" ".join(sim_command.split()[-2:])]
                                       .a_mem.get_str_seq_events())

        elif ("#print persona associative memory (thought)" 
              in sim_command.lower()): 
          # #print the associative memory (thought) of the persona specified in
          # the prompt
          # Ex: #print persona associative memory (thought) Isabella Rodriguez
          ret_str += f'{self.personas[" ".join(sim_command.split()[-2:])]}\n'
          ret_str += (self.personas[" ".join(sim_command.split()[-2:])]
                                       .a_mem.get_str_seq_thoughts())

        elif ("#print persona associative memory (chat)" 
              in sim_command.lower()): 
          # #print the associative memory (chat) of the persona specified in
          # the prompt
          # Ex: #print persona associative memory (chat) Isabella Rodriguez
          ret_str += f'{self.personas[" ".join(sim_command.split()[-2:])]}\n'
          ret_str += (self.personas[" ".join(sim_command.split()[-2:])]
                                       .a_mem.get_str_seq_chats())

        elif ("#print persona spatial memory" 
              in sim_command.lower()): 
          # #print the spatial memory of the persona specified in the prompt
          # Ex: #print persona spatial memory Isabella Rodriguez
          self.personas[" ".join(sim_command.split()[-2:])].s_mem.print_tree()

        elif ("#print current time" 
              in sim_command[:18].lower()): 
          # #print the current time of the world. 
          # Ex: #print current time
          ret_str += f'{self.curr_time.strftime("%B %d, %Y, %H:%M:%S")}\n'
          ret_str += f'steps: {self.step}'

        elif ("#print tile event" 
              in sim_command[:16].lower()): 
          # #print the tile events in the tile specified in the prompt 
          # Ex: #print tile event 50, 30
          cooordinate = [int(i.strip()) for i in sim_command[16:].split(",")]
          for i in self.maze.access_tile(cooordinate)["events"]: 
            ret_str += f"{i}\n"

        elif ("#print tile details" 
              in sim_command.lower()): 
          # #print the tile details of the tile specified in the prompt 
          # Ex: #print tile event 50, 30
          cooordinate = [int(i.strip()) for i in sim_command[18:].split(",")]
          for key, val in self.maze.access_tile(cooordinate).items(): 
            ret_str += f"{key}: {val}\n"

        elif ("call -- analysis" 
              in sim_command.lower()): 
          # Starts a stateless chat session with the agent. It does not save 
          # anything to the agent's memory. 
          # Ex: call -- analysis Isabella Rodriguez
          persona_name = sim_command[len("call -- analysis"):].strip() 
          self.personas[persona_name].open_convo_session("analysis")
        elif ("call -- converse" 
              in sim_command.lower()): 
          # Starts a stateless chat session with the agent. It does not save 
          # anything to the agent's memory. 
          # Ex: call -- analysis Isabella Rodriguez
          persona_name = sim_command[len("call -- converse"):].strip() 
          self.personas[persona_name].open_convo_session("converse")

        elif ("call -- load history" 
              in sim_command.lower()): 
          curr_file = maze_assets_loc + "/" + sim_command[len("call -- load history"):].strip() 
          # call -- load history the_ville/agent_history_init_n3.csv

          rows = read_file_to_list(curr_file, header=True, strip_trail=True)[1]
          clean_whispers = []
          for row in rows: 
            agent_name = row[0].strip() 
            whispers = row[1].split(";")
            whispers = [whisper.strip() for whisper in whispers]
            for whisper in whispers: 
              clean_whispers += [[agent_name, whisper]]

          load_history_via_whisper(self.personas, clean_whispers)

        elif ("call -- summarize sym" in sim_command.lower()):
          personas_str = [persona_name for persona_name, persona in self.personas.items()]
          choice = int(input("Who do you wanna summarize?\nChoose a persona from the available, by index " + str(personas_str)+ ": "))

          _name = personas_str[choice]
          _persona = self.personas[_name]

          self.summarize_all_memories(_persona)
        elif ("call -- agent iss" in sim_command.lower()):
          personas_str = [persona_name for persona_name, persona in self.personas.items()]
          choice = int(input("Who do you wanna know?\nChoose a persona from the available, by index " + str(personas_str)+ ": "))

          _name = personas_str[choice]
          _persona = self.personas[_name]

          print(_persona.scratch.get_str_iss())
          


        #print (ret_str)

      except:
        traceback.print_exc()
        print ("Error.")
        pass


if __name__ == '__main__':
  # rs = ReverieServer("base_the_ville_isabella_maria_klaus", 
  #                    "July1_the_ville_isabella_maria_klaus-step-3-1")
  # rs = ReverieServer("July1_the_ville_isabella_maria_klaus-step-3-20", 
  #                    "July1_the_ville_isabella_maria_klaus-step-3-21")
  # rs.open_server()
  

  wrong_input = True
  while wrong_input:
    emotional = input("Are the characters emotional? [y/n]: ").strip().lower()
    wrong_input = False

    if "y" == emotional:
      emotional = True
    elif "n" == emotional:
      emotional = False
    else:
      wrong_input = True

  origin = input("Enter the name of the forked simulation: ").strip()
  target = input("Enter the name of the new simulation: ").strip()

  rs = ReverieServer(origin, target, emotional)
  rs.open_server()




















































