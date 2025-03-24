import os

class NavelEmotion:
    emo_map = {
            "neutral": [],
            "happy": ["Joy", "Love", "Gratification","Hope", ],
            "sad": ["Remorse", "Fears-confirmed", "Disappointment", "Sorry-for", "Shame"],
            "surprise": ["Distress",  "Fear", "Relief", "Admiration", "Gratitude"],
            "anger": ["Hate", "Resentment", "Anger", "Reproach"],
            "smile": ["Happy-for", "Pride", "Gloating","Satisfaction"],
        }
    
    emo = {"neutral": 0,
    "happy": 0,
    "sad": 0,
    "surprise": 0,
    "anger": 0,
    "smile": 0,}
    
    

    def set_em_from_OCC(self, em, value):
        em_navel = self.get_navel_emotion(em, value)
        self.set_em_from_navel(em_navel, value)
        



    def set_em_from_navel(self,em_navel,value):
        self.emo.update({em_navel:value})

    def get_navel_emotion(self, em, em_value):
            
        if em_value <= 0.2:
            return "neutral"
        keys = self.emo_map.keys()
        for k in keys:
            if em in self.emo_map.get(k):
                return k
        return "random"
    
    def __repr__(self):
        return f"NavelEmotion:(neutral: {self.neutral};happy: {self.happy};sad: {self.sad};surprise: {self.surprise};anger: {self.anger};smile: {self.smile})"
    
    def get_major_emotion(self):

        # Get the key with the maximum value
        max_key = max(self.emo, key=self.emo.get)

        # Get the maximum value
        max_value = self.emo[max_key]

        return max_key, max_value



class UserInterrupt(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

def handler():
    print("OLE")
    #raise UserInterrupt

def get_env_vars():
    f = open(".env", mode = "r")
    lines = f.readlines()
    for line in lines:
        info = line.split("=")
        name = info[0]
        value = info[1].strip("\"").strip()
        os.environ[name] = value

def join_processes(processes):
    #print("JOINING ")
    for p in processes:
        p[0].join()
    return []

def terminate_procs(processes):

    for p in processes:
        try:
            p[0].terminate()
        except Exception as e:
            print("TERMINATING PROCESS = " + str(e))
    return []

def kill_procs(processes):
    #print("KILLING BHENJ ->" + str(processes))
    for p in processes:
        try:
            p[0].kill()
            #print("KILLED (" + str(p) + ")")
        except Exception as e:
            print("TERMINATING PROCESS = " + str(e))
    return []


import numpy as np

class MyEnergyVAD:
    '''
    This class implements a simple VAD algorithm based on the energy of the signal.
    '''

    def __init__(
        self,
        sample_rate: int = 16000,
        frame_length: int = 25,
        frame_shift: int = 20,
        energy_threshold: float = 0.05,
        pre_emphasis: float = 0.95,
    ):
        self.sample_rate = sample_rate
        self.frame_length = frame_length
        self.frame_shift = frame_shift
        self.energy_threshold = energy_threshold
        self.pre_emphasis = pre_emphasis

    def __call__(self, waveform: np.ndarray) -> np.ndarray:
        '''
        Args:
            waveform (np.ndarray): input waveform of shape (num_samples,)

        Returns:
            np.ndarray: VAD output of shape (num_frames,)
        '''

        new_waveform, is_stereo = self._convert_to_mono_if_needed(waveform)

        # Pre-emphasis
        new_waveform = np.append(new_waveform[0], new_waveform[1:] - self.pre_emphasis * new_waveform[:-1])

        # Compute energy
        energy = self.compute_energy(new_waveform)

        # Compute VAD
        vad = self.compute_vad(energy)

        return vad

    def compute_energy(self, waveform: np.ndarray) -> np.ndarray:
        '''
        Args:
            waveform (np.ndarray): input waveform of shape (num_samples,)

        Returns:
            np.ndarray: energy of shape (num_frames,)
            
        '''
        #print("SFL= " +str(self.frame_length/1000))
        #print("SFS = " + str(self.frame_shift/1000))
        #print("SR = " + str(self.sample_rate))
        # Compute frame length and frame shift in number of samples (not milliseconds)
        frame_length = int((self.frame_length/1000) * self.sample_rate )
        frame_shift = int((self.frame_shift/1000) * self.sample_rate )

        #print("FL +" + str(frame_length))
        #print("Fs +_____ > " + str(frame_shift))
        #print("wave sh +> " + str(waveform.shape))




        # Compute energy
        #print("VADDDDD " + str((waveform.shape[0] - frame_length + frame_shift) // frame_shift))
        energy = np.zeros(int((waveform.shape[0] - frame_length + frame_shift) // frame_shift))
        for i in range(energy.shape[0]):
            energy[i] = np.sum(waveform[i * frame_shift : i * frame_shift + frame_length] ** 2)

        return energy

    def compute_vad(self, energy: np.ndarray) -> np.ndarray:
        '''
        Args:
            energy (np.ndarray): energy of shape (num_frames,)

        Returns:
            np.ndarray: VAD output of shape (num_frames,)
        '''
        # Compute VAD
        vad = np.zeros(energy.shape)
        #print("energy!!!!!!! = " + str(energy))
        vad[energy > self.energy_threshold*10e10] = True

        return vad

    def apply_vad(self, waveform: np.ndarray) -> np.ndarray:
        '''
        Args:
            waveform (np.ndarray): input waveform of shape (num_samples,)

        Returns:
            np.ndarray: waveform with VAD applied of shape (num_samples,)
        '''
        processed_waveform, is_stereo = self._convert_to_mono_if_needed(waveform)

        vad = self(processed_waveform)

        shift = self.frame_shift * self.sample_rate // 1000
        new_waveform = []
        for channel in range(waveform.shape[0]):
            channel_waveform = []
            for i in range(len(vad)):
                if vad[i] == 1:
                    channel_waveform.extend(waveform[channel, i * shift : i * shift + shift])
            new_waveform.append(channel_waveform)

        new_waveform = np.array(new_waveform)

        return new_waveform
        
    def _convert_to_mono_if_needed(self, waveform: np.ndarray) -> np.ndarray:
        '''
        Args:
            waveform (np.ndarray): input waveform of shape (num_samples,)

        Returns:
            np.ndarray: waveform with dimension adjusted to (1, num_samples)
            bool: True if the signal was stereo, False otherwise
        '''
        if waveform.ndim == 2 and waveform.shape[0] == 2:
            is_stereo = True
            #print("Warning: stereo audio detected, using only the first channel")
            waveform = waveform[0]
            waveform = waveform[np.newaxis, :]
        else:
            is_stereo = False

        return waveform, is_stereo