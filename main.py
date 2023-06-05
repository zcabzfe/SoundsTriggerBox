# main.py
# The following python file is based on the techniques found at:
# https://realpython.com/python-gui-tkinter/

import tkinter as tk
import os
import re
import threading
import time
from tkinter import messagebox
from twilio.rest import Client
import soundtriggerbox_vosk
from trigger_word_training import *


class Controller:
    def __init__(self, root):
        self.root = root
        self.sound_trigger_instance = soundtriggerbox_vosk
        self.my_application = MyApplication(root, self)
        self.trained_sounds_counter = 0
        self.if_logged_in()
        self.running_thread = None  # new line to keep track of running thread
        self.trained_sounds = set()

    def if_logged_in(self):
        # Check if 'twilio_account_details.json' exists
        if os.path.exists('twilio_account_details.json'):
            with open('twilio_account_details.json', 'r') as file:
                data = json.load(file)

                # Check if all necessary keys exist, and they are not empty
                if all(key in data and data[key] for key in
                       ['account_sid', 'auth_token', 'twilio_number', 'my_phone_number']):

                    # If Twilio details are present, validate them
                    if self.verify_twilio_credentials(data['account_sid'], data['auth_token']) and \
                            self.validate_phone_number(data['twilio_number']) and \
                            self.validate_phone_number(data['my_phone_number']):
                        self.switch_to_interface('main')
                        self.update_button_state()
                        return

        # If not, start from the Twilio details interface
        self.switch_to_interface('twilio')

    def update_button_state(self):
        # Initialize flag
        config_exists = False

        # Check if 'config.json' exists and has the necessary keys
        if os.path.exists('config.json'):
            with open('config.json', 'r') as file:
                data = json.load(file)
                if data.get('user_made_sounds') and data['user_made_sounds'].get('trigger_words') and data[
                     'user_made_sounds'].get('sound_pattern'):
                    config_exists = True

        # If both files are present and valid
        if config_exists:
            self.my_application.start_soundtriggerbox_vosk_button.config(state=tk.NORMAL)
        else:
            self.my_application.start_soundtriggerbox_vosk_button.config(state=tk.DISABLED)

    def save_details(self):
        account_sid = self.my_application.account_sid_entry.get().strip()
        auth_token = self.my_application.auth_token_entry.get().strip()
        twilio_number = self.my_application.twilio_number_entry.get().strip()
        my_phone_number = self.my_application.my_phone_number_entry.get().strip()

        if self.verify_twilio_credentials(account_sid, auth_token) and self.validate_phone_number(
                twilio_number) and self.validate_phone_number(my_phone_number):
            self.save_twilio_account_details(account_sid, auth_token, twilio_number, my_phone_number)
            self.root.after(1000, lambda: messagebox.showinfo("Info", "Logged in."))
            self.switch_to_interface('main')
        else:
            self.my_application.error_label['text'] = "Invalid Twilio credentials or phone numbers. Please try again."

    @staticmethod
    def verify_twilio_credentials(account_sid, auth_token):
        try:
            client = Client(account_sid, auth_token)
            client.api.accounts(account_sid).fetch()
            return True
        except Exception as e:
            print("Error validating Twilio credentials:", str(e))
            return False

    @staticmethod
    def validate_phone_number(phone_number):
        phone_pattern = re.compile(r'^\+\d{1,15}$')
        return phone_pattern.match(phone_number)

    @staticmethod
    def save_twilio_account_details(account_sid, auth_token, twilio_number, my_phone_number):
        twilio_details = {
            "account_sid": account_sid,
            "auth_token": auth_token,
            "twilio_number": twilio_number,
            "my_phone_number": my_phone_number
        }

        save_json(twilio_details, 'twilio_account_details.json')

    def start_training_sound(self, sound_name, number, sys_mode):
        print(self.trained_sounds)
        if sound_name in self.trained_sounds:
            self.my_application.training_text.insert(tk.END,
                                                     f"Sound '{sound_name}' already trained. Please train a different sound.\n")
            return

        def run_training():
            self.my_application.training_text.delete('1.0', tk.END)
            words = []
            for i in range(number):
                self.my_application.training_text.insert(tk.END, f"Say '{sound_name}' for the {i + 1}st time.\n")
                self.my_application.training_text.update_idletasks()
                word = recognise_words()
                words.append(word)
                time.sleep(1)  # delay for user to read the message

            try:
                most_frequent_word = mode(words)
            except StatisticsError:
                most_frequent_word = words[0]

            if sys_mode == 1:
                repeated_element = " ".join([most_frequent_word] * 3)
                update_user_made_sounds("sound_pattern", sound_name, repeated_element)
            elif sys_mode == 2:
                update_user_made_sounds("trigger_words", sound_name, most_frequent_word)
            else:
                self.my_application.training_text.insert(tk.END, "Invalid system mode. Please try again.\n")

            self.my_application.training_text.insert(tk.END, f"Most recognized word for '{sound_name}': {most_frequent_word}\nTraining complete for '{sound_name}'. Proceed to the next one\n")

            # Add sound_name to the set of trained sounds
            self.trained_sounds.add(sound_name)

            # Increase the total training counter
            self.trained_sounds_counter += 1

            # Check if all unique sounds have been trained and if the total training count is at least 4
            if len(self.trained_sounds) >= 4 and self.trained_sounds_counter >= 4:
                time.sleep(2)  # delay before showing messagebox
                messagebox.showinfo("Info", "Training Complete. You can now start the sound trigger.")
                self.switch_to_interface('main')
                # Clear the trained sounds after switching interfaces, so the training can start anew if necessary.
                self.trained_sounds = set()

        threading.Thread(target=run_training).start()

    # Start SoundsTriggerBox Service
    def run_soundtriggerbox_vosk(self):
        self.my_application.start_soundtriggerbox_vosk_button['text'] = 'Stop SoundTriggerBox-Service'
        self.my_application.start_soundtriggerbox_vosk_button['command'] = self.stop_soundtriggerbox_vosk
        self.my_application.start_soundtriggerbox_vosk_button['state'] = tk.NORMAL  # enable button
        self.running_thread = threading.Thread(target=self.sound_trigger_instance.run_soundtriggerbox_vosk)
        self.running_thread.start()
        self.update_status_periodically()

    # Stop SoundsTriggerBox Service
    def stop_soundtriggerbox_vosk(self):
        self.sound_trigger_instance.stop_sound_trigger()
        self.running_thread.join()  # join running thread to stop it
        self.my_application.start_soundtriggerbox_vosk_button['text'] = 'Start SoundTriggerBox-Service'
        self.my_application.start_soundtriggerbox_vosk_button['command'] = self.run_soundtriggerbox_vosk
        self.my_application.start_soundtriggerbox_vosk_button['state'] = tk.NORMAL  # enable button
        self.update_status_periodically()

    # Check running status periodically
    def update_status_periodically(self):
        if self.running_thread is not None:
            print(self.running_thread)
            print(self.running_thread.is_alive())
        if self.running_thread and self.running_thread.is_alive():
            self.my_application.status_label["text"] = "Service Status: Running SoundTriggerBox..."
            # call this method again after 1000 milliseconds
            self.root.after(1000, self.update_status_periodically)
        else:
            self.my_application.status_label["text"] = "Service Status: Not Running"
            self.my_application.start_soundtriggerbox_vosk_button['text'] = 'Start SoundTriggerBox-Service'
            self.my_application.start_soundtriggerbox_vosk_button['command'] = self.run_soundtriggerbox_vosk
            self.my_application.start_soundtriggerbox_vosk_button['state'] = tk.NORMAL  # enable button
            self.running_thread = None

    def disable_service(self):
        self.sound_trigger_instance.stop_sound_trigger()
        if self.running_thread is not None and self.running_thread.is_alive():
            self.running_thread.join()  # join running thread to stop it
        self.my_application.root.quit()

    def move_to_main(self):
        self.switch_to_interface("main")

    def move_to_training(self):
        self.switch_to_interface("train")

    def switch_to_interface(self, interface_name):
        if interface_name == "train":
            self.my_application.clear_interface()
            self.my_application.initialize_train_default_sounds_interface()
        else:
            self.my_application.clear_interface()
            self.my_application.initialize_interface()
            self.update_button_state()


class MyApplication:
    def __init__(self, root, controller):
        self.status_label = None
        self.root = root
        self.controller = controller
        self.initialize_twilio_details_interface()
        self.root.config(bg="#fafafa")
        self.root.title("Sound Trigger Box")  # Add title to the window

    def initialize_interface(self):
        self.create_main_interface()

    def initialize_twilio_details_interface(self):
        self.create_twilio_details_interface()

    def initialize_train_default_sounds_interface(self):
        self.create_train_default_sounds_interface()

    def update_status(self, status_text):
        self.status_label["text"] = "Service Status: " + status_text

    def clear_interface(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def create_twilio_details_interface(self):
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True)

        frame.grid_rowconfigure(0, weight=1)  # Allow row to expand
        frame.grid_rowconfigure(1, weight=1)  # Allow row to expand
        frame.grid_columnconfigure(0, weight=1)  # Allow column to expand
        frame.grid_columnconfigure(1, weight=1)  # Allow column to expand

        self.title_label = tk.Label(frame, text="Sound Trigger Box\nYour Emergency Triggering Voice Assistant",
                                    font=("Arial", 24), bg="#fafafa")
        self.title_label.grid(row=0, column=0, sticky="ew")

        self.account_sid_label = tk.Label(frame, text="Account SID:", font=("Arial", 20))
        self.account_sid_label.grid(row=1, column=0, sticky="ew")
        self.account_sid_entry = tk.Entry(frame)
        self.account_sid_entry.grid(row=1, column=1, sticky="ew")

        self.auth_token_label = tk.Label(frame, text="Auth Token:", font=("Arial", 20))
        self.auth_token_label.grid(row=2, column=0, sticky="ew")
        self.auth_token_entry = tk.Entry(frame)
        self.auth_token_entry.grid(row=2, column=1, sticky="ew")

        self.twilio_number_label = tk.Label(frame, text="Twilio Phone Number:", font=("Arial", 20))
        self.twilio_number_label.grid(row=3, column=0, sticky="ew")
        self.twilio_number_entry = tk.Entry(frame)
        self.twilio_number_entry.grid(row=3, column=1, sticky="ew")

        self.my_phone_number_label = tk.Label(frame, text="Your Phone Number:", font=("Arial", 20))
        self.my_phone_number_label.grid(row=4, column=0, sticky="ew")
        self.my_phone_number_entry = tk.Entry(frame)
        self.my_phone_number_entry.grid(row=4, column=1, sticky="ew")

        self.error_label = tk.Label(frame, text="", fg="red")
        self.error_label.grid(row=5, column=0, columnspan=2, sticky="ew")

        self.save_button = tk.Button(frame, text="Save Details", command=self.controller.save_details, font=("Arial", 20))
        self.save_button.grid(row=6, column=0, columnspan=2, sticky="ew")

        return frame

    def create_main_interface(self):
        frame = tk.Frame(self.root, bg="#fafafa")
        frame.pack(fill=tk.BOTH, expand=True)

        self.title_label = tk.Label(frame, text="Sound Trigger Box\nYour Emergency Triggering Voice Assistant", font=("Arial", 24), bg="#fafafa")
        self.title_label.grid(row=0, column=0, sticky="ew")

        # Add the instructions
        self.instructions_label = tk.Label(frame,
                                           text="Instructions: \n1. Click 'Train Sound Profile' to train your SOUND PROFILE. \n"
                                                "2. Click 'Start SoundTriggerBox-Service' to start the service. \n"
                                                "3. Click 'Quit' to stop the service and exit the program. \n"
                                                "(If you did not train your sound profile, please train it to be able to Start SoundTriggerBox-Service) \n",
                                           font=("Arial", 16),
                                           bg="#fafafa")
        self.instructions_label.grid(row=1, column=0, sticky="ew")

        self.retrain_soundprofile_button = tk.Button(frame, text="Train Sound Profile", font=("Arial", 20),
                                                           command=self.controller.move_to_training)
        self.retrain_soundprofile_button.grid(row=2, column=0, sticky="ew")

        self.start_soundtriggerbox_vosk_button = tk.Button(frame, text="Start SoundTriggerBox-Service",
                                                           font=("Arial", 20),
                                                           command=self.controller.run_soundtriggerbox_vosk,
                                                           state=tk.DISABLED)  # Disabled by default
        self.start_soundtriggerbox_vosk_button.grid(row=3, column=0, sticky="ew")

        self.disable_service_button = tk.Button(frame, text="Quit", font=("Arial", 20),
                                                command=self.controller.disable_service)
        self.disable_service_button.grid(row=4, column=0, sticky="ew")

        self.status_label = tk.Label(self.root, text="Service Status: Not Running")
        self.status_label.pack()

        # Configure grid to expand
        for i in range(5):
            frame.rowconfigure(i, weight=1)
        frame.columnconfigure(0, weight=1)

        return frame

    def create_train_default_sounds_interface(self):
        frame = tk.Frame(self.root, bg="#fafafa")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.title_label = tk.Label(frame, text="Train Default Sounds", font=("Arial", 30), bg="#fafafa")
        self.title_label.grid(row=0, column=0, sticky="ew", pady=10)

        self.title_label1 = tk.Label(frame, text="Please click each button once to complete the training.", font=("Arial", 15), bg="#fafafa")
        self.title_label1.grid(row=1, column=0, sticky="ew", pady=10)

        # configure the column to expand
        frame.grid_columnconfigure(0, weight=1)

        # Create separate buttons for each sound/word
        self.start_training_button_ay = tk.Button(frame, text="Start Training 'ay'", font=("Arial", 20),
                                                  command=lambda: self.controller.start_training_sound("ay", 3, 1))
        self.start_training_button_ay.grid(row=2, column=0, sticky="ew", pady=10)

        self.start_training_button_ah = tk.Button(frame, text="Start Training 'ah'", font=("Arial", 20),
                                                  command=lambda: self.controller.start_training_sound("ah", 3, 1))
        self.start_training_button_ah.grid(row=3, column=0, sticky="ew", pady=10)

        self.start_training_button_ee = tk.Button(frame, text="Start Training 'ee'", font=("Arial", 20),
                                                  command=lambda: self.controller.start_training_sound("ee", 3, 1))
        self.start_training_button_ee.grid(row=4, column=0, sticky="ew", pady=10)

        self.start_training_button_help = tk.Button(frame, text="Start Training 'help'", font=("Arial", 20),
                                                    command=lambda: self.controller.start_training_sound("help", 3, 2))
        self.start_training_button_help.grid(row=5, column=0, sticky="ew", pady=10)

        self.training_text = tk.Text(frame, font=("Arial", 20))
        self.training_text.grid(row=6, column=0, sticky="ew", pady=10)

        return frame


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    app = Controller(root)
    root.mainloop()
