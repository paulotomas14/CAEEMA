from pydub import AudioSegment
import asyncio
import wave
import queue as QUEUE

import pyaudio
#import whisper
from openai import OpenAI
import os
import time
import multiprocessing
from colorama import Fore, Style
from speech_to_text_utils import *

os.environ["OPENAI_API_KEY"] = API_KEY
API_URL = "https://api.openai.com/v1/audio/transcriptions"  # Update if using another API


SAMPLE_RATE = 48000
BYTES_PER_SAMPLE = 2
REC_RATE = 0.3
REC_LIMIT = 2
REQ_CHANNELS = 2
REQ_CHUNK = 1024


class WhisperSTT:
    def __init__(self, audio_client, device):
        self.openAI = OpenAI()
        self.client = audio_client
        self.device = device
        #self.speaking = multiprocessing.Value("i", 0)

    def robot_speak(self, req):

        self.speaking.value = 1
        self.client.robot_speak(req)
        time.sleep(0.8)
        self.speaking.value = 0

    def main(self, ROBOT):
        # echo-client.py

        chunk = REQ_CHUNK  # Record in chunks of 1024 samples
        sample_format = pyaudio.paInt16  # 16 bits per sample
        channels = REQ_CHANNELS
        fs = SAMPLE_RATE  # Record at 44100 samples per second
        filename = "sounds/client.wav"
        queue = self.client.queue
        flag = False
        HOST = self.client.host
        PORT = self.client.port

        p = pyaudio.PyAudio()  # Create an interface to PortAudio
        if ROBOT:
            ind = get_audio_device_index(p, self.device)
        else:
            ind = 15


        #print('Recording')

        text = ""
        time_started = time.time()
        
        # Store data in chunks for 3 seconds
        frames = []  # Initialize array to store frames

        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            input_device_index=ind,
            rate=SAMPLE_RATE,
            input=True,
        )
        new_thresh = adjust_to_noise(ROBOT, self.device, SAMPLE_RATE)
        print("DONE")
        
        

        
        
        start = time.time() - REC_LIMIT-1
        dat = bytearray()
        sim_start = time.time()
        times = []
        final_times = []
        task = None

        main_audio = AudioSegment.silent(duration=REC_RATE)
        all_noise = AudioSegment.silent(duration=REC_RATE)
        main_audio.export("sounds/client.wav", format="wav")
        main_audio.export("sounds/whole_client.wav", format="wav")
        all_noise.export("sounds/whole_noise.wav", format="wav")

        process = None

        process_effector = None

        #device = "odas_1"
        #ind = get_audio_device_index(p, device)
        #print("ODAS 1 = " +str(ind))
        #print(f"Recording from {device}")
        

        

        begin_recording = False
        final_data = bytearray()
            
        requests = []
        try:
            while True:
                start_whisper = False
                empty = False
                
                    


                
                
                
                t = time.time()
                frames = []
                ole = time.time()
                
                frames = []

                if self.client.speaking.value == 0:
                    while ole-t < REC_RATE:
                        try:
                            data = stream.read(chunk)
                            dat.extend(data)
                            frames.append(data)   
                            for i in range(len(data)):
                                times.append(ole)
                            ole = time.time()
                        except Exception as e:
                            print("COULD NOT RECORD STREAM: "+ str(e))


                    filename2 = "sounds/output_i.wav"
                    
                    MAX = 60 * chunk
                    if len(dat)>MAX:
                        dat = dat[-MAX:len(dat)]
                    
                    byte_data = b"".join(frames)
                    wf = wave.open(filename2, 'wb')
                    wf.setnchannels(1)
                    wf.setsampwidth(p.get_sample_size(sample_format))
                    wf.setframerate(fs)
                    wf.writeframes(byte_data)
                    wf.close()

                    #myaudio = AudioSegment.from_wav(filename2)
                    
                    
                    silen = check_silence(dat, new_thresh)
                    
                    
                    if  silen == False:
                        

                        is_playing = True
                        begin_recording = True
                        start = time.time()
                        flag = True
                        
                    else:
                        is_playing = False


                    if is_playing:
                        if process is not None:
                            process.terminate()  
                        if process_effector is not None:
                            process_effector.terminate()
                        queue.put("!!!DUMP!!!")              
                        print("...")

                        final_data.extend(dat)
                        final_times.extend(times)
                        dat = bytearray()
                        times = []
                        try:
                            #self.client.speaking.value = 1
                            self.client.play_sound("on")
                            #self.client.speaking.value = 0
                    
                            self.client.s.sendto("LIST".encode("utf-8"),(self.client.host, self.client.port))
                            time_start = time.time()
                            self.client.requests = []
                            self.client.queue.put("!!!DUMP!!!")
                            error = False
                        except OSError:
                            error = True
                        
                    else:
                        if begin_recording:
                            if time.time()-start >= REC_LIMIT:
                                begin_recording = False
                                start_whisper=True
                                time_started = time.time()

                            print("...")
                            final_data.extend(dat)
                            final_times.extend(times)
                            dat = bytearray()
                            times = []
                        



                        
                    
                    if start_whisper:
                        
                        
                        wf = wave.open(filename, 'wb')
                        wf.setnchannels(1)
                        wf.setsampwidth(p.get_sample_size(sample_format))
                        wf.setframerate(fs)
                        wf.writeframes(final_data)
                        wf.close()

                        
                        
                        process = multiprocessing.Process(target=self.get_whisper_text, args=(filename, time_started))
                        process.start()
                        

                        dat = bytearray()
                        times = []
                else:
                    #print("SPEAKING")
                    pass
            


        except KeyboardInterrupt:
            if process is not None and process.is_alive() == False:
                process = process.join()
                process = None 
            if process_effector is not None and process_effector.is_alive() == False:
                process_effector = process_effector.join()
                process_effector = None 
            self.client.s.close()
            return

                

       
        
    
    def get_whisper_text(self,filename,time_started):
                
        res = self.transcribe_api(filename)

        myaudio = AudioSegment.from_wav(filename)
        whole_audio = AudioSegment.from_wav("sounds/whole_client.wav")
        whole_audio = whole_audio+myaudio
        whole_audio.export("sounds/whole_client.wav", format="wav")
        if res != "":
            leave = self.client.get_dialogue(res, time_started)
            self.listening = False
            if leave:
                #stream.closed = True
                #print("RETURNED")
                return True
        return False



        '''cont = self.client.send_result_to_server(result, time_started)
        if cont:
            self.client.recieve_from_server( time_started)'''
    

    def transcribe_api(self, filename):
        

        t = time.time()
        
        audio_file= open(filename, "rb")
        transcription = self.openAI.audio.transcriptions.create(
                                        model="whisper-1", 
                                        file=audio_file,
                    )
        #print("Transcription = "+ str(transcription.text))
        #time.sleep(10)
        print("WHISPER TAKES =" + str(time.time()-t))
        return transcription.text
