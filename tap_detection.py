#https://github.com/xSparfuchs/clap-detection/blob/master/clap-detection.py
import pyaudio
import struct
import math
import time
import numpy as np
import time

LOWER_TAP_THRESHOLD = 0.1
UPPER_TAP_THRESHOLD = 0.3  
FORMAT = pyaudio.paInt16 
SHORT_NORMALIZE = (1.0/32768.0)
CHANNELS = 1
RATE = 44100  
INPUT_BLOCK_TIME = 0.05
INPUT_FRAMES_PER_BLOCK = int(RATE*INPUT_BLOCK_TIME)
# if we get this many noisy blocks in a row, increase the threshold
OVERSENSITIVE = 15.0/INPUT_BLOCK_TIME                    
# if we get this many quiet blocks in a row, decrease the threshold
UNDERSENSITIVE = 120.0/INPUT_BLOCK_TIME 
# if the noise was longer than this many blocks, it's not a 'tap'
MAX_TAP_BLOCKS = 0.15/INPUT_BLOCK_TIME

# how many seconds of quiet before we consider the
# current tap ended, and reset the tap counter
# How many taps before we consider it a goal
PERIOD_TIME = 5
GOAL_TAPS = 3


def get_rms( block ):
    # RMS amplitude is defined as the square root of the 
    # mean over time of the square of the amplitude.
    # so we need to convert this string of bytes into 
    # a string of 16-bit samples...

    # we will get one short out for each 
    # two chars in the string.
    count = len(block)/2
    format = "%dh"%(count)
    shorts = struct.unpack( format, block )

    # iterate over the block.
    sum_squares = 0.0
    for sample in shorts:
        # sample is a signed short in +/- 32768. 
        # normalize it to 1.0
        n = sample * SHORT_NORMALIZE
        sum_squares += n*n

    return math.sqrt( sum_squares / count )

class TapTester(object):
    def __init__(self):
        print("Initializing TapTester...")
        self.pa = pyaudio.PyAudio()
        self.stream = self.open_mic_stream()
        self.lower_tap_threshold = 0
        self.upper_tap_threshold = 0
        self.noisycount = MAX_TAP_BLOCKS + 1
        self.quietcount = 0
        self.errorcount = 0
        self.start_time = 0
        self.tap_count = 0
        self.cooldown_end_time = 0
        self.train_taps()  # Start training process

    def stop(self):
        print("Closing the stream.")
        self.stream.close()

    def find_input_device(self):
        print("Searching for an input device...")
        device_index = None
        for i in range(self.pa.get_device_count()):
            devinfo = self.pa.get_device_info_by_index(i)
            print("Device {}: {}".format(i, devinfo["name"]))

            for keyword in ["mic", "input"]:
                if keyword in devinfo["name"].lower():
                    print("Found an input: device {} - {}".format(i, devinfo["name"]))
                    device_index = i
                    return device_index

        if device_index is None:
            print("No preferred input found; using default input device.")
        return device_index

    def open_mic_stream(self):
        print("Opening microphone stream...")
        device_index = self.find_input_device()
        stream = self.pa.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            input_device_index=device_index,
                            frames_per_buffer=INPUT_FRAMES_PER_BLOCK)
        print("Microphone stream opened.")
        return stream
    
    def train_taps(self):
        print("Training mode: you will need to tap 10 times")
        amplitudes = []
        # This is the min value that should be accepted as the sound
        min_tap_amplitude = 0.05

        # Training for 10 taps
        print("Tap!!!")
        while len(amplitudes) < 10:  
            try:
                block = self.stream.read(INPUT_FRAMES_PER_BLOCK)
                amplitude = get_rms(block)

                if amplitude > min_tap_amplitude and time.time() > self.cooldown_end_time:
                    amplitudes.append(amplitude)
                    print("Tap registered amplitude: {:.2f}".format(amplitude))       
                    # Cooldown to avoid echo
                    self.cooldown_end_time = time.time() + 0.5
                    print("Tap!!!") 


            except Exception as e:
                print("Error during training: {}".format(e))
            

        # Calculate mean and standard deviation
        mean_amplitude = np.mean(amplitudes)
        std_deviation = np.std(amplitudes)

        # Set the thresholds based on the mean and standard deviation
        self.lower_tap_threshold = max(mean_amplitude - (std_deviation * 1.5), min_tap_amplitude)
        self.upper_tap_threshold = mean_amplitude + (std_deviation * 1.5)
        print("Training complete. Lower threshold: {:.2f}, Upper threshold: {:.2f}".format(
            self.lower_tap_threshold, self.upper_tap_threshold))
        print("Detecting taps")

    def tapDetected(self):
        print("3 Taps detected!")
        

    def listen(self):
        try:
            block = self.stream.read(INPUT_FRAMES_PER_BLOCK)
            # print("Reading a block of audio data.")
        except Exception as e:
            self.errorcount += 1
            print("({}) Error recording: {}".format(self.errorcount, e))
            self.noisycount = 1
            return

        amplitude = get_rms(block)
        #print("Amplitude: {:.2f}".format(amplitude))

        if time.time() - self.start_time > PERIOD_TIME and self.tap_count > 0:
            self.tap_count = 0
            self.start_time = 0
            print("Tap count reset.")
        if self.lower_tap_threshold <= amplitude <= self.upper_tap_threshold:
            self.quietcount = 0
            self.noisycount += 1

            if self.start_time == 0:
                self.start_time = time.time()
                print("Start time:", self.start_time)


            self.tap_count += 1
            print("Tap count:", self.tap_count)
            if self.tap_count >= GOAL_TAPS:
                self.tapDetected()
                self.tap_count = 0
                self.start_time = 0
                return
            

            # print("Noisy block detected. Noisy count:", self.noisycount)
        else:
            # print(f"max tap blocks:{MAX_TAP_BLOCKS}")
            self.noisycount = 0
            self.quietcount += 1
            # print("Quiet block detected. Quiet count:", self.quietcount)


if __name__ == "__main__":
    tt = TapTester()

    for i in range(1000):
        tt.listen()