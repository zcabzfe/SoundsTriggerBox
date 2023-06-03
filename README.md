# SoundsTriggerBox

SoundsTriggerBox is a voice-assistant application designed to empower individuals with Amyotrophic Lateral Sclerosis (ALS) or Motor Neurone Disease (MND) through sound recognition. Recognizing that vocal abilities vary greatly among individuals with ALS or MND, SoundsTriggerBox allows users to train the system to recognize their unique sound profile, ensuring adaptability to diverse vocal characteristics. The application leverages Vosk for speech recognition and PyAudio for capturing sound. In emergency situations, when a predefined sound trigger is detected, the system can send an alert via SMS using the integrated Twilio API. This project, developed in Python with a user-friendly tkinter graphical interface, is positioned as a vital tool to enhance safety and independence for individuals living with ALS or MND by providing a hands-free, voice-activated emergency response system.


To run SoundsTriggerBox service:

1. Clone the repo: git clone https://github.com/zcabzfe/SoundsTriggerBox.git

2. Make sure you have Python installed. If not yet, install python by following this guide: https://realpython.com/installing-python/

2. Install requirements.txt. Run pip install -r requirements.txt in terminal.(To download a particular package, such as Vosk, simply enter "pip install vosk" into your command prompt or terminal. This will automatically download the latest version of the package, irrespective of the version specified.)

3. Run the main.py.

4. Enter correct twilio account details (If you do not have a twilio account follow this guide from 2:01 to 3:00: https://www.youtube.com/watch?v=ywH2rsL371Q)

5. Follow instructions to Train your sound profile 

6. Start SoundTriggerBox Service (Say "stop" or click on "Stop SoundTriggerBox Service" to stop the service or "Quit" to quit the program)

