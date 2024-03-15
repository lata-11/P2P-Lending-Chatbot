import telebot
from telebot import types
import json

API_KEY = '6410553908:AAFPXhYc8Yh0jcs-w_U1qIpuYI2RCkKSCHA'
bot = telebot.TeleBot(API_KEY)

with open('src/intents.json', 'r') as file:
    intents = json.load(file)

@bot.message_handler(commands=["startpoll"])
def start_poll(message):
    create_poll(message)

def create_poll(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(types.KeyboardButton("Yes"), types.KeyboardButton("No"))
    bot.send_message(message.chat.id, "A member of your group has requested for a loan of 1000 rupees. Are you willing to give?", reply_markup=markup)

    # Register a handler to handle the user's response to the poll
    bot.register_next_step_handler(message, handle_poll_response)

def handle_poll_response(message):
    if message.text.lower() == "yes":
        print("here")
        bot.reply_to(message, "You voted 'Yes'! Thank you for lending a loan :)")
    elif message.text.lower() == "no":
        bot.reply_to(message, "You voted 'No'! Thank you for your response.")
