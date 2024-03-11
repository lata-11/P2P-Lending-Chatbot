import telebot
from neural_intents import GenericAssistant
import sys
from io import StringIO
import pandas as pd


API_KEY = '6410553908:AAFPXhYc8Yh0jcs-w_U1qIpuYI2RCkKSCHA'

bot = telebot.TeleBot(API_KEY, parse_mode=None)


@bot.message_handler(commands=["start", "hello"])
def send_hello_message(msg):
    bot.reply_to(msg, "Hello! This is a peer-to-peer lending bot!")

# borrow loan


@bot.message_handler(commands=["loan", "borrow, credit"])
def borrow_loan(msg):
    loan_amount = bot.reply_to(msg, "How much do you want to borrow?")
    bot.register_next_step_handler(loan_amount, borrow_loan_amount)


def borrow_loan_amount(msg):
    loan_amount = msg.text
    bot.reply_to(
        msg, f"Your loan request of {loan_amount} rupees is under process. You will be informed within 30 minutes.")


def bye(msg):
    bot.send_message(msg.chat.id, "Goodbye!")
    sys.exit(0)


def thanks(msg):
    bot.send_message(msg.chat.id, "You're welcome:)")


def default_handler(msg):
    bot.reply_to(msg, "I did not understand.")


# send notification

# create group

#mapping
mappings = {
    'wants_loan': borrow_loan,
    'wants_amount': borrow_loan_amount,
    'bye': bye,
    None: default_handler
}

# training model
assistant = GenericAssistant(
    'src/intents.json', mappings, "peer_to_peer_lending_bot")

assistant.train_model()
assistant.save_model()


bot.polling()
