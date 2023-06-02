# trigger_word_training.py

import pyaudio
from statistics import mode, StatisticsError
from vosk import Model, KaldiRecognizer
from config import *

# Clear the user_made_sounds dictionary
# clear_user_made_sounds()

# Load the current configuration
config = load_json('config.json')
model = Model("vosk-model-small-en-us-0.15")
recognizer = KaldiRecognizer(model, 16000)


def recognise_words():
    text = ''
    cap = pyaudio.PyAudio()
    stream = cap.open(
        format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192
    )
    stream.start_stream()

    streaming = True

    while streaming:
        data = stream.read(4096)

        if recognizer.AcceptWaveform(data):
            text = recognizer.Result()
            text = text[14:-3]
            print(text)
            streaming = False
    stream.stop_stream()
    return text


def train_sounds(sound_name, number, sys_mode):
    words = []

    while number != 0:
        # print("say " + sound_name)
        word = recognise_words()
        words.append(word)
        number = number - 1

    try:
        most_frequent_word = mode(words)
    except StatisticsError:
        # print("No unique mode found. Using the first word as the most frequent word.")
        most_frequent_word = words[0]

    if sys_mode == 1:
        # "ah" will become "ah ah ah"
        repeated_element = " ".join([most_frequent_word] * 3)
        update_user_made_sounds("sound_pattern", sound_name, repeated_element, 'config.json')  # TO DO: create user_made_sounds_dict
    elif sys_mode == 2:
        update_user_made_sounds("trigger_words", sound_name, most_frequent_word, 'config.json')  # TO DO: create user_made_sounds_dict
    else:
        print("Invalid system mode. Please try again.")


# def train_default_sounds(number):
#     #print("Do not worry if what you say does not match the sound exactly.")
#     train_sounds("ay", number, 1)
#     train_sounds("ah", number, 1)
#     train_sounds("ee", number, 1)
#
#
# def train_default_triggerwords(number):
#     #print("Do not worry if what you say does not match the sound exactly.")
#     train_sounds("help", number, 2)


# def train_customization(number, user_trigger_inputs, sys_mode):
#     print("Do not worry if what you say does not match the sound exactly.")
#     for trigger in user_trigger_inputs:
#         train_sounds(trigger, number, sys_mode)


# def train_customized_triggerwords_sound(number, triggerwords, soundpattern):
#     train_customization(number, soundpattern, 1)
#     train_customization(number, triggerwords, 2)


# def get_trigger_words(sys_mode):
#     trigger_words = []
#     if sys_mode == 1:
#         print("Enter sound(like ah,ey,ee) one by one. Type 'done' when you have finished entering the words.")
#     elif sys_mode == 2:
#         print("Enter trigger words(like help) one by one. Type 'done' when you have finished entering the words.")
#
#     while True:
#         word = input("Enter a trigger word/sound: ").strip()
#         if word.lower() == "done":
#             break
#         else:
#             trigger_words.append(word)
#
#     while True:
#         print("\nCurrent trigger words/sound:")
#         for index, word in enumerate(trigger_words):
#             print(f"{index}: {word}")
#
#         action = input(
#             "Type 'delete' to remove a trigger word, 'confirm' to finalize the list, or 'add' to add a new word: ").strip().lower()
#
#         if action == "delete":
#             index_to_delete = int(input("Enter the index of the trigger word/sound to remove: "))
#             if 0 <= index_to_delete < len(trigger_words):
#                 removed_word = trigger_words.pop(index_to_delete)
#                 print(f"Removed '{removed_word}' from the list.")
#             else:
#                 print(f"Invalid index. Please try again.")
#         elif action == "add":
#             word_to_add = input("Enter the trigger word/sound to add: ").strip()
#             trigger_words.append(word_to_add)
#             print(f"Added '{word_to_add}' to the list.")
#         elif action == "confirm":
#             break
#         else:
#             print("Invalid input. Please try again.")
#
#     return trigger_words


# def triggerword_and_soundpattern_training():
#     train_default_sounds(3)
#     train_default_triggerwords(3)
#
#     while True:
#         customization_choice = input("Do you want to customize your trigger words or sound pattern? (y/n): ").lower()
#         if customization_choice == "y":
#             break
#         elif customization_choice == "n":
#             return
#         else:
#             print("Invalid input. Please enter 'y' or 'n'.")
#
#     while True:
#         action = input("Choose customization option: 1. Sound pattern, 2. Trigger words, 3. Both: ")
#         if action == "1":
#             triggerwords = get_trigger_words(1)
#             train_customization(3, triggerwords, 1)
#             break
#         elif action == "2":
#             triggerwords = get_trigger_words(2)
#             train_customization(3, triggerwords, 2)
#             break
#         elif action == "3":
#             soundpattern = get_trigger_words(1)
#             triggerwords = get_trigger_words(2)
#             train_customized_triggerwords_sound(3, triggerwords, soundpattern)
#             break
#         else:
#             print("Invalid input. Please try again.")
