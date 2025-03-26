from environment.frontend_server.pepper.utils import join_processes, kill_procs, terminate_procs, get_env_vars
from multiprocessing import Process, Queue
from environment.frontend_server.pepper.robot_server import RobotServer, TERMINATE_KEYWORDS

import time
from colorama import Fore, Style
from pathlib import Path
import json
import os
from pydub import AudioSegment
import sys
import socket
from datetime import datetime




HOST = "127.0.0.1"
PORT = 65433  # Port to listen on (non-privileged ports are > 1023)



def sense(emotional, queue, agent,fs_storage, sim_code):
        print("Waiting on connection...")
        s_1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s_1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            s_1.bind((HOST,PORT))

        except OSError as e:
            print("ERROR NO CONNECTION = " + str(e))
        


    
        robot_server = RobotServer(s_1)
        robot_server.handshake(emotional)
        p = Process(target=robot_server.main, args= (queue,))
        p.start()
        ##print("LEFT AUDIO PROCESS")
        return p, robot_server


def interview(emotional, input_queue, output_queue, human, fs_storage, sim_code, step, chat, persona, partner):

    inp =  ""
    full_resp = ""
    inp_time = None
    full_resp_time = None
    queue = Queue()
    data = {"input": ""}
    robot_server_process, robot_server_object = sense( emotional, queue, human, fs_storage, sim_code )
    #print(robot_server_object)
    
    
    processes = []
    try:

        while TERMINATE_KEYWORDS not in data["input"].lower():
            #print("waiting on pack= "+str(queue))
            package = queue.get()
            #print("DATA = "+ str(package))
            if package != "<None>":
                done = package[0]
                data = package[1]
                #print("DONE = "+str(done))
            
                if done == True:



                    inp = data["input"]
                    inp_time = data["input_time"]


                    if TERMINATE_KEYWORDS in data["input"]:
                        break


                    resp = data["resp"] + "!!!END!!!"
                    full_resp += data["resp"]
                    resp_time = data["resp_time"]
                    if full_resp_time is None:
                        full_resp_time = resp_time
                    emo = data["emo"]


                    #affect - change this to world

                    processes = join_processes(processes)

                    

                    if "!!!LISTENING!!!" not in data["input"]:
                        effector( human, inp, resp, robot_server_object, emo )
                        

                elif done == "Ongoing":



                    inp = data["input"]
                    inp_time = data["input_time"]


                    if TERMINATE_KEYWORDS in data["input"]:
                        break


                    resp = data["resp"] 
                    full_resp+=resp
                    resp_time = data["resp_time"]
                    emo = data["emo"]
                    if full_resp_time is None:
                        full_resp_time = resp_time

                    #affect - change this to world

                    #processes = join_processes(processes)

                    

                    if "!!!LISTENING!!!" not in data["input"]:
                        effector( human, inp, resp, robot_server_object, emo )
                        

                elif done == "ACKNOWLEDGED":
                    if TERMINATE_KEYWORDS in data["input"]:
                        break
                    inp_time = data.get("input_time")
                    chat[0].append([f"{partner}", inp,  inp_time])
                    chat[0].append([f"{persona}", full_resp, full_resp_time])
                    resp_ = f"[{datetime.now()}]\nRESPONSE: " + str(full_resp) + "\n"
                    print(Fore.CYAN + resp_)
                    print(Style.RESET_ALL)
                    chat[1].append(resp_)
                    chat[2].append((datetime.now(), None, (time.time() - inp_time) , None,None, None, inp, full_resp, "" ))
                    inp = ""
                    full_resp = ""
                    full_resp_time = None
                    
                    

                else:
                    
                    #data.update({"input":data["input"]})


                    processes = end_procs(processes, data, input_queue, output_queue)
                    #print("HERE!")



                    if "!!!LISTENING!!!" not in data["input"]:
                        #print("NOT HGEHBEHB")
                        inp += data["input"]
                        #print("data input = " + str(data["input"]))
                        if TERMINATE_KEYWORDS in data["input"].lower():
                            #print("BROKE HERE")
                            break
                        data["input"] = inp        
                        #print("ROBOTB LISTEN = " + str(inp))
                        p = Process(target=interview_agent, args= (input_queue, output_queue, queue, human, data,fs_storage, sim_code, step))
                        processes.insert(0, (p, "interview",time.time()))
                        ##print("INSERTED PROCESS = " + str(processes))
                        p.start()
                

                
    except Exception as e:
        print("ROBOT PROCESS EXCEPTION : " + str(e))
                
    #print("LEAVING ROBOT PROCESS = " + str(robot_server_process))
    #robot_server_process.terminate()
    #robot_server_process.kill()
    robot_server_process.join()
    processes = join_processes(processes)
    #print("OLE")
    #join_processes(processes)
    interview_agent(input_queue, output_queue, queue, human, {"input": "end_convo"},fs_storage, sim_code, step)
    print("LEFT ROBOT PROCESS")
    sys.exit(0)




def end_procs(processes, data, input_queue, output_queue):
    new_procs = []
    for p in processes:
        #print("PPPPPP" + str(p))
        if p[1]=="interview":
            #print("KILLL")
            input_queue.put(data)
            output_queue.put(None)
            p[0].join()
        else:
            new_procs.append(p)

    return new_procs


def interview_agent(input_queue, output_queue, queue, human, data, fs_storage,sim_code, step) -> str:
        
    #print("INTERVIEW START")
    get_dialogue_response(input_queue, output_queue, data, fs_storage, sim_code, step, queue, human)
    

def get_dialogue_response(input_queue, output_queue, data, fs_storage, sim_code, step, queue, human):

    #print("GET DIALOGUE RESPONSE START")
    input_queue.put(data)
    #print(data)
    
    if data["input"] != "end_convo":
        return wait_for_response(output_queue, step, queue, data, human)

def wait_for_response(output_queue, step, queue, data, human):

    #time.sleep()
    env_retrieved = False
    while env_retrieved==False:
        #print("HERE WAITING FOR AGENT RESPONSE! "+ str(output_queue))
        try:
            package = output_queue.get()
            #print("NEW ENV FROM ROBOT SIDE = " + str(new_env))
            if(package is not None):

                resp_time = time.time()
                new_env = package[1]
                resp = new_env.get("resp")
                if resp != "":
                    emo = resp.split("|")[0]
                    true_resp = resp.split("|")[1]
                    hu = human.split(" ")[0]
                    h = f"{hu},"
                    h2 = f", {hu}"
                    true_resp = true_resp.replace(h2, "")

                    true_resp = true_resp.strip(h)
                else:
                    emo = "None - 0" 
                    true_resp = ""

                new_env.update({"resp_time":resp_time, "resp": true_resp, "emo":emo})

                queue.put((package[0],new_env ))

                if package[0] == True:

                    env_retrieved = True


            else:
                #print("LEFT HERE HELO")
                return
        except Exception as e:
            print("NO RESPONSE ON ROBOT SIDE = " + str(e))


   

    

    


def effector(human, inp, resp, robot_server, emo):

    response = resp.strip('\n').strip(" ").strip('\"')
    #print("RESPONSEEEEEEEEEEEEEEEEEEEEEEE = " + str(response))
    Message = f"""<<DIALOGUE>>{response}<<EMOTION>>{emo}"""
    robot_server.send_response(Message)
    



