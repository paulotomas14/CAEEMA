import numpy as np
import time
from openai import OpenAI
import pyaudio


def get_current_time() -> int:
    """Return Current Time in MS.

    Returns:
        int: Current Time in MS.
    """

    return int(round(time.time() * 1000))
    


def get_audio_device_index(p: pyaudio.PyAudio, device: str):
    info = p.get_host_api_info_by_type(pyaudio.paALSA)

    for i in range(0, info["deviceCount"]):
        dev = p.get_device_info_by_host_api_device_index(0, i)

        if device == dev["name"]:
            return i

    raise ValueError(f"Device '{device}' does not exist")

def adjust_thresh(all_means, t):
    mod_e = np.mean(np.abs(all_means))
    #print(all_means)
    #print(mod_e)
    return mod_e + t
    

def check_silence(data, thresh):
    #amp = get_mean_aplitude(data)
    amplitude = np.frombuffer(data, np.int16)
    amp = max(np.abs(amplitude))
    #print(data)
    #print("AMP = " + str(amp))
    #print("Tresh = " + str(thresh))
    return amp < thresh

def get_max_aplitude(data):
    amplitude = np.frombuffer(data, np.int16)
    amp = max(np.abs(amplitude))
    return amp

def adjust_to_noise(ROBOT, device, SAMPLE_RATE):
    p = pyaudio.PyAudio()  # Create an interface to PortAudio
    if ROBOT:
            ind = get_audio_device_index(p, device)
    else:
        ind = 15

    stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            input_device_index=ind,
            rate=SAMPLE_RATE,
            input=True,
        )
    t = time.time()
    amps = []
    dat = bytearray()
    print("Adjusting sound sensitivity")
    while time.time() -t <= 1:
        #print(".", end=" ")
        data = stream.read(1024)
        dat.extend(data)
        amps.append(get_max_aplitude(data))
    
    tresh = adjust_thresh(amps, 0)

    while check_silence(dat, tresh) == False:
        tresh += 200
    
    stream.close()
    return tresh

    
