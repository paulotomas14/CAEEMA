import pyaudio
import queue
from google.cloud import speech
import os
import multiprocessing
import asyncio
import time
from speech_to_text_utils import *
import re
import sys
import random
import logging

logging.getLogger("urllib3").setLevel(logging.CRITICAL)

#logging.basicConfig(level=logging.DEBUG)




LANG = "en-US"


# Audio recording parameters
STREAMING_LIMIT = 60000
SAMPLE_RATE = 48000 # Hz 
DURATION = 10
CHUNK_SIZE = int(SAMPLE_RATE/DURATION)

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
RESET = "\033[0m"










class ResumableMicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(
        self: object,
        rate: int,
        chunk_size: int,
        audio_client: object, 
        dev: str,
        ROBOT: bool,
        ) -> None:
        """Creates a resumable microphone stream.

        Args:
        self: The class instance.
        rate: The audio file's sampling rate.
        chunk_size: The audio file's chunk size.

        returns: None
        """
        self._rate = rate
        self.chunk_size = chunk_size
        self._num_channels = 1
        self._buff = queue.Queue()
        self.closed = True
        self.start_time = get_current_time()
        self.restart_counter = 0
        self.audio_input = []
        self.last_audio_input = []
        self.result_end_time = 0
        self.is_final_end_time = 0
        self.final_request_end_time = 0
        
        self.bridging_offset = 0
        self.last_transcript_was_final = False
        self.new_stream = True
        self._audio_interface = pyaudio.PyAudio()
        p = self._audio_interface
        self.device = dev
        self.thresh = None

        '''info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        index = 0
        host_api_filter = pyaudio.paALSA


        for i in range(0, numdevices):
            if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'), p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels'))
                index = i

        microphones = [idx for idx in range(p.get_device_count())
                    if (device_info := p.get_device_info_by_index(idx)) and
                    device_info.get('maxInputChannels') > 0 and
                    ((host_api_filter == 0) or (device_info.get('hostApi') == host_api_filter))]

        print("MICROPHONES:")
        for mic in microphones:
            print(mic)
        print("^^^^^^^^^^^^^^^^")'''
        self.ROBOT = ROBOT
        if ROBOT:
            ind = get_audio_device_index( self._audio_interface, self.device)
        else:
            ind = 15
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=self._num_channels,
            rate=self._rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            input_device_index = ind, 
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.client = audio_client
        self.listening = False


    

    

    
    
    

    def __enter__(self: object) -> object:
        """Opens the stream.

        Args:
        self: The class instance.

        returns: None
        """
        self.closed = False
        return self

    def __exit__(
        self: object,
        type: object,
        value: object,
        traceback: object,
    ) -> object:
        """Closes the stream and releases resources.

        Args:
        self: The class instance.
        type: The exception type.
        value: The exception value.
        traceback: The exception traceback.

        returns: None
        """
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(
        self: object,
        in_data: object,
        *args: object,
        **kwargs: object,
    ) -> object:
        """Continuously collect data from the audio stream, into the buffer.

        Args:
        self: The class instance.
        in_data: The audio data as a bytes object.
        args: Additional arguments.
        kwargs: Additional arguments.

        returns: None
        """
        #self._buff.put(in_data)
        #print("SPEAKING")
        if self.client.speaking.value == 0:
            self._buff.put(in_data)
        else:
            fake_data = bytearray(random.getrandbits(8) for _ in range(len(in_data)))
            self._buff.put(fake_data)
        return None, pyaudio.paContinue

    def generator(self: object) -> object:
        """Stream Audio from microphone to API and to local buffer

        Args:
            self: The class instance.

        returns:
            The data from the audio stream.
        """
        while not self.closed:
            data = []

            if self.new_stream and self.last_audio_input:
                chunk_time = STREAMING_LIMIT / len(self.last_audio_input)

                if chunk_time != 0:
                    if self.bridging_offset < 0:
                        self.bridging_offset = 0

                    if self.bridging_offset > self.final_request_end_time:
                        self.bridging_offset = self.final_request_end_time

                    chunks_from_ms = round(
                        (self.final_request_end_time - self.bridging_offset)
                        / chunk_time
                    )

                    self.bridging_offset = round(
                        (len(self.last_audio_input) - chunks_from_ms) * chunk_time
                    )

                    for i in range(chunks_from_ms, len(self.last_audio_input)):
                        data.append(self.last_audio_input[i])

                self.new_stream = False

            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            self.audio_input.append(chunk)



            if chunk is None:
                return
            data.append(chunk)

           


            #yield speech.StreamingRecognizeRequest(audio_content=chunk)
            # Now consume whatever other data's still buffered.
            while True:
                try:
                    #print("HERE GETTING CHUNKIES")
                    chunk = self._buff.get(block=False)

                    if chunk is None:
                        return
                    data.append(chunk)
                    self.audio_input.append(chunk)

                except queue.Empty:
                    break

            #yield speech.StreamingRecognizeRequest(audio_content=b"".join(data))
            #print("AMA HERE")
            yield b"".join(data)

    def handle_response(self, responses):


        stream = self
        time_start = time.time()
        try:
            for response in responses:

                if get_current_time() - stream.start_time > STREAMING_LIMIT:
                    stream.start_time = get_current_time()
                    break

                if not response.results:
                    continue

                result = response.results[0]
                #print(result)

                if not result.alternatives:
                    continue

                #transcript = result.alternatives[0].transcript

                result_seconds = 0
                result_micros = 0

                if result.result_end_time.seconds:
                    result_seconds = result.result_end_time.seconds

                if result.result_end_time.microseconds:
                    result_micros = result.result_end_time.microseconds

                stream.result_end_time = int((result_seconds * 1000) + (result_micros / 1000))

                corrected_time = (
                    stream.result_end_time
                    - stream.bridging_offset
                    + (STREAMING_LIMIT * stream.restart_counter)
                )
                # Display interim results, but with a carriage return at the end of the
                # line, so subsequent lines will overwrite them.




                result = response.results[0]
                if self.client.speaking.value != 1:
                    if result.is_final:
                        if self.listening==True:
                            if self.client.speaking.value != 1:
                                stream.is_final_end_time = stream.result_end_time
                                stream.last_transcript_was_final = True
                                if self.client is not None:
                                    res = result.alternatives[0].transcript

                                    if res != "":
                                        if self.client.speaking.value == 0:
                                            self.client.speaking.value = 1
                                        time_start = time.time()
                                        if self.ROBOT:
                                            if len(self.client.participant_info)>0:
                                                vec = self.client.participant_info[len(self.client.participant_info)-1]
                                            else:
                                                vec = ()
                                        else:
                                            vec = "Participant Info:(CartVec3d(x=1.2,y=0.5,z=2.4),0.8,PersonFacialExpression(neutral=0.8,happy=0.9,sad=0.1,surprise=0.2,anger=0.3))"

                                            
                                        leave = self.client.get_dialogue(res, time_start, vec)
                                        

                                        self.listening = False
                                        if leave:
                                            stream.closed = True
                                            print("RETURNED")
                                            return True
                            
                        
                    else:
                        print("...")
                        if self.listening==False:
                            if self.client.speaking.value != 1:
                                self.listening = True
                                self.client.play_sound("on")
                                self.client.s.sendto("LIST".encode("utf-8"),(self.client.host, self.client.port))
                                time_start = time.time()
                                stream.last_transcript_was_final = False
                                #self.client.requests = []
                                #self.client.queue.put("!!!DUMP!!!")

                else:
                    self.listening = False
        except Exception as e:
            print(f"Error during streaming ole: {e}")
        print("RETURNED")
        return False


class GoogleSTT:

    def __init__(self, audio_client, device):
        self.client = audio_client
        self.process = None
        self.device = device
        

    def listen_print_loop(self: object, responses: object, stream: object) -> None:
        """Iterates through server responses and prints them.

        The responses passed is a generator that will block until a response
        is provided by the server.

        Each response may contain multiple results, and each result may contain
        multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
        print only the transcription for the top alternative of the top result.

        In this case, responses are provided for interim results as well. If the
        response is an interim one, print a line feed at the end of it, to allow
        the next result to overwrite it, until the response is a final one. For the
        final one, print a newline to preserve the finalized transcription.

        Arg:
            responses: The responses returned from the API.
            stream: The audio stream to be processed.
        """
        try:
            counter = 0
            for response in responses:
                if get_current_time() - stream.start_time > STREAMING_LIMIT:
                    stream.start_time = get_current_time()
                    break

                if not response.results:
                    continue

                result = response.results[0]

                if not result.alternatives:
                    continue

                transcript = result.alternatives[0].transcript

                result_seconds = 0
                result_micros = 0

                if result.result_end_time.seconds:
                    result_seconds = result.result_end_time.seconds

                if result.result_end_time.microseconds:
                    result_micros = result.result_end_time.microseconds

                stream.result_end_time = int((result_seconds * 1000) + (result_micros / 1000))

                corrected_time = (
                    stream.result_end_time
                    - stream.bridging_offset
                    + (STREAMING_LIMIT * stream.restart_counter)
                )
                # Display interim results, but with a carriage return at the end of the
                # line, so subsequent lines will overwrite them.

                if result.is_final:
                    sys.stdout.write(GREEN)
                    sys.stdout.write("\033[K")
                    sys.stdout.write(str(corrected_time) + ": " + transcript + "\n")

                    stream.is_final_end_time = stream.result_end_time
                    stream.last_transcript_was_final = True
                    self.client.queue.put((transcript, "love", 0, time.time()))

                    # Exit recognition if any of the transcribed phrases could be
                    # one of our keywords.
                    if re.search(r"\b(exit|quit)\b", transcript, re.I):
                        sys.stdout.write(YELLOW)
                        sys.stdout.write("Exiting...\n")
                        stream.closed = True
                        break
                else:
                    sys.stdout.write(RED)
                    sys.stdout.write("\033[K")
                    sys.stdout.write(str(corrected_time) + ": " + transcript + "\r")
                    counter+=1
                    #sys.stdout.write("COUNTER =" + str(counter))

                    stream.last_transcript_was_final = False
        except Exception as e:
            print(e)

    

    
    def main(self, ROBOT):
        """start bidirectional streaming from microphone input to speech API"""
        #new_thresh = adjust_to_noise(ROBOT, self.device, SAMPLE_RATE)
        #new_thresh = 6700



        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "cred.json"



        speech_client = speech.SpeechClient()
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            language_code=LANG,
            enable_automatic_punctuation=True
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config, interim_results=True
        )

        

        mic_manager = ResumableMicrophoneStream(SAMPLE_RATE, CHUNK_SIZE, self.client, self.device, ROBOT)
        #mic_manager.thresh = new_thresh

        sys.stdout.write(YELLOW)
        sys.stdout.write('\nListening, say "Terminate chat" to stop.\n\n')
        sys.stdout.write("End (ms)       Transcript Results/Status\n")
        sys.stdout.write("=====================================================\n")
        sys.stdout.write(RESET)
        t = time.time()
        
        with mic_manager as stream:
            try:
                while not stream.closed:
                    sys.stdout.write(YELLOW)
                    sys.stdout.write(
                        "\n" + str(STREAMING_LIMIT * stream.restart_counter) + ": NEW REQUEST\n"
                    )
                    sys.stdout.write(RESET)

                    stream.audio_input = []
                    stream._buff = queue.Queue()
                    audio_generator = stream.generator()


                    requests = (
                        speech.StreamingRecognizeRequest(audio_content=content, )
                        for content in audio_generator
                    )
                    

                    
                    try:
                        responses = speech_client.streaming_recognize(streaming_config, requests)
                    except Exception as e:
                        print(f"Error: {e}")
                        continue

                    #print(len(responses))


                    # Now, put the transcription responses to use.
                    #self.listen_print_loop(responses, stream)
                    leave = stream.handle_response(responses)
                    #if leave:
                        #return

                    if stream.result_end_time > 0:
                        stream.final_request_end_time = stream.is_final_end_time
                    stream.result_end_time = 0
                    stream.last_audio_input = []
                    stream.last_audio_input = stream.audio_input
                    stream.audio_input = []
                    stream.restart_counter = stream.restart_counter + 1

                    if not stream.last_transcript_was_final:
                        sys.stdout.write("\n")
                    stream.new_stream = True
                    #print("LEFT!")
            except Exception as e:
                print(e)
                stream.close()

            