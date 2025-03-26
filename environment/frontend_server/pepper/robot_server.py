import time
from openai import OpenAI
import scipy.io.wavfile as wav
import socket
#from reverie.backend_server.utils import *
import numpy as np
import soundfile as sf
import sys

from multiprocessing import Process

TERMINATE_KEYWORDS = "terminate"




class RobotServer:
    t = time.time()
    pause_time = 0
    client = None
    sub_process = None
    first_chunk = True
    agent = None
    kill_now = False
    host = None
    port = None
    client = None
    socket = None

    emo_map = {
            "neutral": [],
            "happy": ["Joy", "Love", "Gratification","Hope", ],
            "sad": ["Remorse", "Fears-confirmed", "Disappointment", "Sorry-for", "Shame"],
            "surprise": ["Distress",  "Fear", "Relief", "Admiration", "Gratitude"],
            "anger": ["Hate", "Resentment", "Anger", "Reproach"],
            "smile": ["Happy-for", "Pride", "Gloating","Satisfaction"],
        }

    def __init__(self, socket):
        self.socket = socket

    def get_navel_emotion(self, em, em_value):
        if self.emotional:
            if em_value <= 0.2:
                return "neutral"
            keys = self.emo_map.keys()
            for k in keys:
                if em in self.emo_map.get(k):
                    return k
        return "random"

    def handshake(self, emo):
        handshake = False

        while not handshake:
            try:
                print("Waiting on handshake format...")
                data, client = self.socket.recvfrom(1024)
                #print("data eejejej = " + str(data))
                #dar split do handshake 
                self.client = client
                #print("CLIENT = " + str(client))
                self.socket.sendto(f"AKN:{emo}".encode("utf-8"),self.client)
                handshake = True

            except Exception as e:
                print(e)
                pass
            



    def main(self, queue):        
        
        
        chunk = 1024


        pr = None
        # Example usage:

        stuff = ""
        # Store data in chunks for 3 seconds
        
            
        self.t = time.time()
        print("SERVER LISTENING")
        
        while True:
            try:
                
                data, addr = self.socket.recvfrom(chunk)
                if len(data)==4:
                    stuff = data.decode()
                    #print("STUF == "+ str(stuff))
                    if stuff== "SENT":
                        break
                    elif stuff=="LIST":
                        #print("jndejnenjenj")
                        package = (False,{"input":"!!!LISTENING!!!", "input_time":time.time()})
                        queue.put(package)
                        if pr != None:
                            ##print("HERE PROMP UB " + str(p))
                            pr.kill()
                            pr = None
                    elif stuff=="ACKN":
                        #print("jndejnenjenj")
                        package = ("ACKNOWLEDGED",{"input":"ACKN", "input_time":time.time()})
                        queue.put(package)
                        if pr != None:
                            ##print("HERE PROMP UB " + str(p))
                            pr.kill()
                            pr = None
                else:
                    stuff = data.decode()

                    splt = stuff.split("|")

                    inp = splt[0]
                    inp_time = splt[1]
                    vec = splt[2]



                    #print("NENEEJJE")
                    package = (False,{"input":inp, "input_time":inp_time, "participant_info":vec})
                    #print("HELLO PACK = " + str(package))
                    queue.put(package)
                    if TERMINATE_KEYWORDS in stuff.lower():
                        break

            except Exception as e:
                #print("RECEIVING PROMB =" + str(e))
                data = []

           
            
        #self.conn.close()
        self.socket.close()
        try:
            if pr != None:
                pr.kill()
            #self.sub_process.kill()
        except Exception as e:
            print("COULD NOT CLOSE Transcription =  "+ str(e))
        print("LEFT AUDIO SERVER")
        self.socket.close()
        sys.exit(0)


    def get_sub_processs(self):
        return self.sub_process
    
    def send_response(self, response):
        self.socket.sendto(response.encode("utf-8"), self.client)

        

    
    