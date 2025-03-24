import asyncio
#import whisper
import socket
import time
import multiprocessing
from colorama import Fore, Style
from google_speech_to_text import GoogleSTT
from whisper_speech_to_text import WhisperSTT
import logging
import queue as QUEUE
import random
from pydub import AudioSegment
from pydub.playback import play



#logging.basicConfig(level=logging.DEBUG)

language = "en"




WHISPER = False
ROBOT = True
if ROBOT:
    import navel
else:
    from gtts import gTTS
    from playsound import playsound





#HOST = "190.168.0.103"  # Standard loopback interface address (localhost)
HOST = "192.168.171.17"
#HOST = "192.168.144.17"
#HOST = "192.168.171.17"

PORT = 65433  # Port to listen on (non-privileged ports are > 1023)
DEBUG_SINGLE = False
X_MIDDLE = 300
MAXIMUM_X_DISTANCE_WHEN_GAZING_AT_USER = 100
MAX_EMOTION = 10
WAIT_UNTIL_NEW_SEARCH = 10



class NavelClient:

    def __init__(self, HOST, PORT):
  
        self.device = "odas_1"

        self.queue = multiprocessing.Queue()
        self.kill_now = False
        #print("START")
        self.host = HOST
        self.port = PORT
        self.TERMINATE_KEYWORDS = "terminate"
        self.speaking = multiprocessing.Value("i", 0)
        self.output_process = None
        self.requests = []
        if ROBOT:
            self.robot = True

        self.emotional = False
        self.found_person = True
        self.found_person_uuid = None
        self.found_person_px = None
        self.finished_receiving = True
        self.task_counter = 0
        self.manager = multiprocessing.Manager()
        self.participant_info = self.manager.list()
        self.searches = []

        self.gesture_thresholds = {
            "none": 0,
            "calm": 0.1,
            "normal": 0.3,
            "animated":0.6,
            "crazy":0.8
        }

        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)     

        msg = f"CLIENT=Navel"
        msg = msg.encode("utf-8")
        error = True

        
        if not DEBUG_SINGLE:            
            while error:

                try:
                    self.s.sendto(msg,(HOST, PORT))
                    print("SENT HANDSHAKE")
                    self.s.settimeout(5.0)
                    msg, serv = self.s.recvfrom(1024)
                    print("MESSAGE = " + str(msg))
                    ack = msg.decode().split("AKN:")
                    if len(ack)>0:
                        error = False
                    emo = ack[1]
                    #print(ack)
                    #print(emo)
                    if emo =="True":
                        self.emotional=True

                    
                except Exception as e:
                    print("EXCEPTION ROBOT CLIENT =  " + str(e))
                    error = True
            self.s.settimeout(None)



    async def disable_automatic_expressions(self, robot):
        
        await robot.config_set("cns_fer_cont_t1", 0, navel.DataType.U32)
        await robot.config_set("cns_fer_cont_t2", 0, navel.DataType.U32)
        await robot.config_set("cns_fer_peak_t1", 0, navel.DataType.U32)
        await robot.config_set("cns_fer_peak_t2", 0, navel.DataType.U32)
        await robot.config_set("cns_fer_overlay_inc", 0, navel.DataType.F32)
        await robot.config_set("cns_fer_overlay_max", 0, navel.DataType.F32)
        await robot.config_set("cns_fer_overlay_peak_min", 0, navel.DataType.F32)
        await robot.config_set("cns_fer_peak_max", 0, navel.DataType.F32)
        #pass

    async def enable_automatic_expressions(self, robot):

        
        await robot.config_set("cns_fer_cont_t1", 1, navel.DataType.U32)
        await robot.config_set("cns_fer_cont_t2", 1, navel.DataType.U32)
        await robot.config_set("cns_fer_peak_t1", 1, navel.DataType.U32)
        await robot.config_set("cns_fer_peak_t2", 1, navel.DataType.U32)
        await robot.config_set("cns_fer_overlay_inc", 1, navel.DataType.F32)
        await robot.config_set("cns_fer_overlay_max", 1, navel.DataType.F32)
        await robot.config_set("cns_fer_overlay_peak_min", 1, navel.DataType.F32)
        await robot.config_set("cns_fer_peak_max", 1, navel.DataType.F32)
        #pass

    async def counter_look(self):
        #print("COUNTER LOOK AT START")
        try:
            task = asyncio.current_task()
            self.searches.append(task)
            counter = time.time()
            t = time.time()-counter
            while t < 3:
                t = time.time()-counter
                await asyncio.sleep(0.1)
                #print("TRYING LOOK AT = " + str(t))
            for elem in self.searches:
                #print(elem)
                if elem is not task:
                    elem.cancel()
            self.searches = []
            #print("counter look done")
        except asyncio.exceptions.CancelledError:
            #print("COUNTER LOOK CANCELLED")
            pass

    async def look_at(self, robot, found_person_px, x):
        #print("LOOK AT START")
        try:
            #task = asyncio.current_task()
            #self.searches.append(task)
            await robot.look_at_px(found_person_px, x)
            '''for elem in self.searches:
                if elem is not task:
                    elem.cancel()
            self.searches = []'''

        except asyncio.exceptions.CancelledError:
            #print("LOOK AT CANCELLED")
            pass
        #print("LOOK AT DONE")



    async def wait_and_search(self, robot, move:bool): 
        full_facing = False
        offset = 5
        while full_facing == False:
            found_person = False
            #print("AQUI")
            while not found_person:
                #print("SEARCH")
                data = await self.search(robot, move)
                #print("FOUND PERSON UUID = "+ str(move))
                if data is not None:
                    found_person = True
                    found_person_px = data.persons[0].landmarks.nose
                    self.found_person_px = found_person_px
                        
                    await self.look_at(robot, found_person_px, 0.6)

                    #print("ALI")
                        

                        
                    
                    try:
                        if len(data.persons)>0:
                            #print("DATA")
                            #print("Person found:", data.persons[0].uuid)
                            try:
                                gaze = data.persons[0].gaze
                                gaze_overlap = data.persons[0].gaze_overlap
                                facial_expression = data.persons[0].facial_expression
                                self.participant_info.append((gaze, gaze_overlap, facial_expression))
                                #print(self.participant_info[len(self.participant_info)-1])
                            except Exception as e:
                                print("COULDN'T ADD PERSON INFO: " + str(e))

                            found_person_px = data.persons[0].landmarks.nose
                        else:
                            if move:
                                continue
                            else:
                                #print("WAIT AND SEARCH DONE")
                                return 

                    except Exception as e:
                        print("Perception error:" + str(e))
                        continue
                    if move:
                        if found_person_px.x-X_MIDDLE<0:
                            angle_2 = -offset
                        else:
                            angle_2 = offset
                        #print(found_person_px.x - X_MIDDLE)
                        if abs(found_person_px.x-X_MIDDLE) > MAXIMUM_X_DISTANCE_WHEN_GAZING_AT_USER:

                            await robot.rotate_base(angle_2, 40, 20)
                        else:
                            if abs(found_person_px.x-X_MIDDLE) > MAXIMUM_X_DISTANCE_WHEN_GAZING_AT_USER/2:
                                offset *=0.5
                                await robot.rotate_base(angle_2, 40, 20)
                            else:
                                full_facing = True
                                #print("WAIT AND SEARCH DONE")
                                return 
                    else:
                        #print("WAIT AND SERACH DONE 3")
                        return

                else:
                    self.found_person_px = None
                    if move:
                        continue
                    else:
                        #print("wait and search done ")
                        return

        #print("wait and search done 2")


    async def rotate_base_wrapper_cacth(self, robot, x,y,z):
        #print("HERE ROT")
        try:
            #print(self.found_person_px)
            if self.found_person_px is None:
                #print("ROTATE NOW")
                current_task = asyncio.current_task()
                self.searches.append(current_task)
                await robot.rotate_base(x, y, z)
        except asyncio.exceptions.CancelledError:
            #print("TASK ROTATE CANCELLED ")
            pass
        #print("ROTATE DONE")


                    #await
    async def get_person(self, robot, current_task):
        #print("GET PERSON")
        current_task = asyncio.current_task()
        self.searches.append(current_task)
        try:
            data = await robot.next_frame()
            #print("data 1 = " + str(len(data.persons)))
            if len(data.persons)>0:
                #print("Person found:", data.persons[0].uuid)
                for task in self.searches:
                    if task is not current_task:
                        #print(task)     
                        try:
                            task.cancel()
                        except asyncio.exceptions.CancelledError:
                            print("Task canceled")
                self.searches = []
        except asyncio.exceptions.CancelledError:
            #print("GET PERSON TASK CANCELLED")
            pass
        #print("GET PERSON DONE")
        


    async def search(self, robot, move:bool):
        #walk = robot.move_base(0.5, 0.1)
        found = False
        angle = -90

        while not found:

            try:
                #current_task = asyncio.current_task()  # This is main()

                #await self.get_person(robot, current_task)
                data = await robot.next_frame()
                #print(len(data.persons))
                if len(data.persons)>0:
                    #print("Person found:", data.persons[0].uuid)
                    return data
            except Exception as e:
                print("Perception error:" + str(e))
            if move:
                current_task = asyncio.current_task()  # This is main()
                            
                asyncio.gather(self.rotate_base_wrapper_cacth(robot,angle, 70, 50), self.get_person(robot, current_task)) 

                data = await robot.next_frame()
                #print("Data 2 = "+ str( len(data.persons)))
                if len(data.persons)>0:
                    #print("Person found 2:", data.persons[0].uuid)
                    return data

                
                asyncio.gather( self.rotate_base_wrapper_cacth(robot,-angle, 70, 50), self.get_person(robot, current_task)) 

                data = await robot.next_frame()
                #print(len(data.persons))
                if len(data.persons)>0:
                    #print("Person found 3:", data.persons[0].uuid)
                    return data
                #print("ROTATING!!!")
                angle *=2
            else:
                return None
        return None
    
    def play_sound(self:object, name:str):
        sound = AudioSegment.from_file(f"{name}.mp3")
        if name == "on":
            sound += 20
        else:
            sound+= 10
        # Play the sound
        #if name == "off":
        #self.speaking.value = 1
        play(sound)
        #time.sleep(0.5)
        #if name == "off":
        #self.speaking.value = 0


    async def behavior_loop(self,q, robot):


        #print("HANDLE OUTPUT")
        
        if ROBOT:
            await robot.head_facial_expression(neutral=1)

            await self.disable_automatic_expressions(robot)
            #if self.emotional:
                #await self.disable_automatic_expressions(robot)

            #else:
                #await self.enable_automatic_expressions(robot)
            

            await self.wait_and_search(robot, True)

            self.speaking.value = 1
            await robot.say("Hello!")  # after finds person
            time.sleep(2)
            self.speaking.value = 0


        #print("HELLO!!!!!")
        counter = None
        while True:
            empty = False
            #await robot.look_at_px(self.found_person_uuid, 0.8)
            #print("BEGIN LOOP")
            if ROBOT:
                if self.found_person_px is None:
                    if counter is None:
                        counter = time.time()
                else:
                    counter = None
                if counter:
                    delta = time.time() - counter 
                    #print("DELTA =  " + str(delta))
                    if delta > WAIT_UNTIL_NEW_SEARCH:
                        await self.wait_and_search(robot, True)
                    else:
                        await self.wait_and_search(robot, False)
                else:
                    await self.wait_and_search(robot, False)
                


            #print("HERE 2")
            while empty==False:
                try:
                    msg = q.get_nowait()
                    #if msg is not None:
                        #print("MSG = " + str(msg))
                    if msg == False:
                        return
                    if msg!=True:
                        if msg != "!!!DUMP!!!":
                            self.requests.append(msg)

                        
                        else:
                            self.requests = []
                            empty = True
                            current_task = asyncio.current_task()  # This is main()
                            for task in asyncio.all_tasks():
                                if task is not current_task:
                                    task.cancel()
                            if ROBOT:
                                await robot.rotate_arms(0, 0)
                                #self.speaking.value = 1
                                #await robot.say("Sorry, what?")
                                #time.sleep(0.5)
                                #self.listening = True
                                #self.speaking.value = 0
                                await robot.tilt_base(0, 0)
                                await robot.head_facial_expression(neutral=1)

                    
                except QUEUE.Empty as e:
                    empty = True
            
            if len(self.requests)>0:
                
                req = self.requests.pop(0)
                #print("REQUEST = " + str(req))

                
                t = time.time()
                
                #time.sleep(0.1)
                await self.robot_speak(req, robot)
                #self._buff = queue.Queue()
                #print("SAID DONE IN = " + str(time.time()-t))


    async def start_behavior_loop(self):
        if ROBOT:
            async with navel.Robot() as robot:
                await self.behavior_loop(self.queue, robot)
        else:
            await self.behavior_loop(self.queue, None)

       

    def terminate_tts_process(self):
        if self.output_process is not None and self.output_process.is_alive():
            print("TERMINATE OUTPUT")
            self.queue.put("!!!DUMP!!!")
            self.output_process.terminate()
            self.output_process = None


    def get_dialogue(self, res, time_start, vec):
        cont = self.send_result_to_server( res, time_start, vec)     
        print("My dialogue: " + str((res, time_start, vec)))
        if cont:
            #self.process = multiprocessing.Process(target=self.client.recieve_from_server, args=( time_start,))
            #self.process.start()
            self.recieve_from_server( time_start)
            return False
        else:
            return True

    



    def send_result_to_server( self, result, time_started, vec):
        error = True
        s = self.s
        queue = self.queue

        info = str(vec)

        message = f"{result}|{time_started}|{info}"
        
        while error:
            try:
                s.sendto(message.encode("utf-8"), (HOST, PORT))
                error = False
                queue.put(True)

            except OSError as e:
                error = True
                print(e)

        if self.TERMINATE_KEYWORDS in result.lower():
            queue.put(False)
            return False
        print("sent")
        
        return True

    def send_akn_to_server( self):
        error = True
        s = self.s
        
        while error:
            try:
                s.sendto("ACKN".encode("utf-8"), (HOST, PORT))
                error = False
                print("SENT ACKNOWLEDGE")

            except OSError as e:
                error = True
                print(e)
        
    def normalize(self, value, min_value, max_value):
        return (value - min_value) / (max_value - min_value)


    def recieve_from_server(self, time_started):
        error = False
        s = self.s
        queue = self.queue
        self.play_sound("off")
        self.requests = []


        while not error:
            try:
                message, client_adress = s.recvfrom(1024)
                #print(time.time()-time_started)
                #print("MESSAGE = "+ str(message.decode()))
                mess = message.decode().split("<<DIALOGUE>>")[1]
                dialogue = mess.split("<<EMOTION>>")[0]
                emotion = mess.split("<<EMOTION>>")[1]
                #print(emotion)
                emotion_value = float(emotion.split(" - ")[1])
                emotion_name = emotion.split(" - ")[0]
                end= dialogue.split("!!!END!!!")
                if dialogue == "!!!END!!!":
                    diag = dialogue
                else:
                    diag = end[0]

                if diag != "":
                    diag = diag.strip("\"")
                    package = (diag, emotion_name, emotion_value, time_started)

                    #print("PUT PACKAGE = " + str(package))
                    queue.put(package)
                if dialogue== "!!!END!!!":
                    error = True

                
                #print("TIME IT TOOK = " + str(time.time()-time_started))
                #time_started = time.time()
                

            except OSError as e:
                print(e)
                pass



        return

    def get_gesture(self, value):
        for k in self.gesture_thresholds.keys():
            thresh = self.gesture_thresholds.get(k)
            #print("Thresh = " + str(thresh))
            #print("Value = "+ str(float(value)))
            if thresh is not None and float(value) >= thresh:
                return k
        return "random"
    
    async def gesticulate(self, value, robot):
        try:
            self.task_counter+=1
            if ROBOT:
                #gesticulate = random.choice([True,False])
                gesticulate=True
            else: 
                gesticulate = False
                #await asyncio.sleep(1)

            #print("Gesticulating = " + str(gesticulate))
            if gesticulate:

                gesture = self.get_gesture(value)
                print("GESTURE = " + str(gesture))
                degrees = 20
                motion = 0

                if gesture == "none":
                    motion = 20

                
                elif gesture == "calm":
                    motion = 30
                
                elif gesture == "normal":
                    motion = 40
                
                elif gesture == "animated":
                    motion = 50
                
                elif gesture == "crazy":
                    motion = 60
                else:
                    #motion = random.randint(0,60)
                    motion = 0

                
                left_arm_addon = random.randint(0,motion) * -1
                right_arm_addon = random.randint(0,motion) * -1
                left = degrees+ left_arm_addon
                right = degrees+right_arm_addon
                #print("LEFT ARM = " + str(left))
                #print("RIGHT ARM = " + str(right))
                await robot.rotate_arms( left, right)
                await asyncio.sleep(0.2)
                left_arm_addon = random.randint(0,motion) * -1
                right_arm_addon = random.randint(0,motion) * -1
                left = degrees- left_arm_addon
                right = degrees- right_arm_addon
                #print("LEFT ARM 2= " + str(left))
                #print("RIGHT ARM 2= " + str(right))
                await asyncio.sleep(0.2)
                await robot.rotate_arms(max(0,left), max(0,right))
            self.task_counter-=1
        except asyncio.CancelledError:
            print("Task gesticulate cancelled")



    async def emote_tilt_base(self, robot, value, x):
        #print("EMOTE VALUE = " + str(value))
        em_value = value/3
        if x:
            await robot.tilt_base(-em_value, 0)
            await asyncio.sleep(0.2)
            await robot.tilt_base(em_value, 0)
            await asyncio.sleep(0.2)
            #await robot.tilt_base(em_value, 0)
        else:
            await robot.tilt_base(0,-em_value)
            await asyncio.sleep(0.2)
            await robot.tilt_base(0, em_value)
            await asyncio.sleep(0.2)
            #await robot.tilt_base(0, em_value)
        

        
    
    async def emote(self, navel_emotion, em_value, robot):
        try:
            self.task_counter+=1
            if navel_emotion == "neutral":
                print(Fore.GREEN)
            elif navel_emotion == "happy":
                print(Fore.YELLOW)
            elif navel_emotion == "sad":
                print(Fore.BLUE)
            elif navel_emotion == "surprise":
                print(Fore.MAGENTA)
            elif navel_emotion == "anger":
                print(Fore.RED)
            elif navel_emotion == "smile":
                print(Fore.CYAN)
            elif navel_emotion == "random":
                print(Style.RESET_ALL)
            

            

            if ROBOT:
                '''if navel_emotion == "random":
                    if self.speaking.value == 0:
                        navel_emotion = random.choice(["neutral", "happy", "sad", "surprise", "anger", "smile"])
                    else:
                        navel_emotion = None
                    print("RANDOM EMOTION = " + str(navel_emotion))'''

                if navel_emotion == "neutral":
                    print("EMOTING = " +  str(navel_emotion))          

                    await robot.head_facial_expression(neutral=em_value)
                    await self.emote_tilt_base(robot, em_value, True)

                elif navel_emotion == "happy":
                    print("EMOTING = " +  str(navel_emotion))          

                    await robot.head_facial_expression(happy=em_value)
                    await self.emote_tilt_base(robot, em_value, True)


                elif navel_emotion == "sad":
                    print("EMOTING = " +  str(navel_emotion))          

                    await robot.head_facial_expression(sad=em_value)
                    await self.emote_tilt_base(robot, em_value, False)


                elif navel_emotion == "surprise":
                    print("EMOTING = " +  str(navel_emotion))          

                    await robot.head_facial_expression(surprise=em_value)
                    await self.emote_tilt_base(robot, em_value, True)


                elif navel_emotion == "anger":
                    await robot.head_facial_expression(anger=em_value)
                    await self.emote_tilt_base(robot, em_value, True)

                elif navel_emotion == "smile":
                    print("EMOTING = " +  str(navel_emotion))          

                    await robot.head_facial_expression(smile=em_value)
                    await self.emote_tilt_base(robot, em_value, True)

            await asyncio.sleep(0.2)       
            self.task_counter-=1
        except asyncio.CancelledError:
            print("Task emote cancelled")



    async def diag(self, text, robot):
        try:
            #if self.speaking.value == 0:
                #self.speaking.value = 1
            #else:
                #time.sleep(1)

            self.task_counter+=1
            print("Started saying ")
            t=time.time()
            await robot.say(text)
            print("Finished saying = " + str(time.time()-t))
            self.task_counter-=1
            #print("END TASK COUNTER = " + str(self.task_counter))
        except asyncio.CancelledError:
            print("Task diag cancelled")





    

    async def robot_speak(self,msg, robot):
        #print(msg[0])
        try:
            diag = msg[0].strip("\"").strip()
            #print(diag)
            em_name = msg[1]
            em_value = msg[2]
            if self.emotional == False:
                em_value = random.randint(0,MAX_EMOTION)

            time_started = msg[3]


            #need to study the normalization max values in this case

            #print("EM VALUE = " + str(em_value))
            
            em_value = min(em_value, MAX_EMOTION)
            em_value = self.normalize(em_value, 0, MAX_EMOTION)
            #print("EM VALUE = " + str(em_value))

            if diag == "!!!END!!!":
                self.finished_receiving = True
                #print((-robot._arms[0],-robot._arms[1]))
                while self.task_counter != 0:
                    #print("AWAIT TASK COUNTER = " + str(self.task_counter))
                    await asyncio.sleep(0)

                if self.finished_receiving:
                    print(diag)
                    self.speaking.value = 0
                    self.send_akn_to_server()

                if ROBOT:
                    asyncio.gather(robot.rotate_arms(0,0), robot.tilt_base(0,0),robot.head_facial_expression(neutral=1))
                #else:
                    #await asyncio.sleep(0.5)

                
                return
            else:
                #self.task_counter +=1
                #print("TASK COUNTER UP = " + str(self.task_counter))

                self.finished_receiving = False


            navel_emotion = em_name

            #await self.emote(navel_emotion, em_value, robot)
            
            print("TOOK: " + str(time.time()- time_started))

            if ROBOT:
                asyncio.gather( self.emote(navel_emotion, em_value, robot), self.diag(diag,robot), self.gesticulate(em_value, robot))

            else:
                await self.emote(navel_emotion, em_value, None)
                # Convert text to speech
                tts = gTTS(text=diag, lang=language, slow=False)
                # Save the output to an audio file
                tts.save("output.mp3")
                playsound("output.mp3")

            print(f"{diag} -> {em_value} - {em_name}")
            print(Style.RESET_ALL)

        except asyncio.CancelledError:
            print("Task robot speak cancelled")

        

            #time.sleep(2)
        
   

    
    async def force_cancel(self, task, max_tries=10):
        # keep track of the number of times tried
        tries = 0
        # keep trying to cancel the task
        while not task.done():
            # check if we tried too many times
            if tries >= max_tries:
                raise RuntimeError(f'Failed to cancel task {task} after {max_tries} attempts.')
            # request the task cancel
            task.cancel()
            # update attempt count
            tries += 1
            # give the task time to cancel
            try:
        # Wait for task to finish or be canceled
                await task
            except asyncio.CancelledError:
                print("Task has been canceled.")





    #async def transcribe(path):
    def tts_process(self):
        if WHISPER:
            whisper_stt = WhisperSTT(self, self.device)
            whisper_stt.main(ROBOT)
        else:
            google_stt = GoogleSTT(self, self.device)
            google_stt.main(ROBOT)
        '''
        while True:
            print("awake")
            time.sleep(5)'''

    
    def starts_tts_process(self):
        if self.output_process is None:
            self.output_process = multiprocessing.Process(target=self.tts_process)
            self.output_process.start()


    



if __name__ == "__main__":
    
    '''if WHISPER == False and ROBOT == False:
        multiprocessing.set_start_method("spawn")'''


    client = NavelClient(HOST, PORT)


    

    client.starts_tts_process()
    try:


        asyncio.run(client.start_behavior_loop())
        #while True:
            #time.sleep(0.1)
    except KeyboardInterrupt:
        client.terminate_tts_process()
