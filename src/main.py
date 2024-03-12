import telebot
from neural_intents import GenericAssistant
import sys
import re


API_KEY = '6410553908:AAFPXhYc8Yh0jcs-w_U1qIpuYI2RCkKSCHA'

bot = telebot.TeleBot(API_KEY, parse_mode=None)


@bot.message_handler(commands=["start", "hello"])
def send_hello_message(msg):
    bot.reply_to(msg, "Hello! This is a peer-to-peer lending bot!")


@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    print(f"Received message: {message.text}")
    add_reply, prob, reply_msg = assistant.request(message.text, message)
    print(F"Probability: {prob}")
    if add_reply:
        bot.reply_to(message, str(reply_msg))
        
#greet
def send_greet(msg):
    bot.reply_to(msg, "Hello! This is a peer-to-peer lending bot!")

# borrow loan
def borrow_loan(msg):
    user_id = msg.from_user.id
    group_id = msg.chat.id

    loan_msg = bot.reply_to(msg, "How much money do you want to borrow?")
    bot.register_next_step_handler(loan_msg, lambda msg: process_loan_request(msg, user_id, group_id))


def process_loan_request(msg, user_id, group_id):
    loan_amount = extract_numeric_value(msg.text)

    if loan_amount is not None:
        response = f"Your loan request of {loan_amount} rupees is under process. You will be informed within 30 minutes."
        bot.reply_to(msg, response)

        send_loan_notification(group_id, user_id, loan_amount)
    else:
        bot.reply_to(msg, "Invalid amount. Please enter a numeric value greater than zero.")
        borrow_loan(msg)


def extract_numeric_value(sentence):
    matches = re.findall(r'\b\d+\b', sentence)
    
    if matches:
        return float(matches[0])
    else:
        return None

def get_group_members(group_id):
    #Will add logic to get members from mongo db group
    pass

def bye(msg):
    bot.send_message(msg.chat.id, "Goodbye!")
    bot.stop_polling()
    sys.exit(0)


def thanks(msg):
    bot.send_message(msg.chat.id, "You're welcome:)")


def default_handler(msg):
    bot.reply_to(msg, "I did not understand.")


# send notification
def send_loan_notification(group_id, sender_id, loan_amount):
    members = get_group_members(group_id)
    notification_msg = f"User {sender_id} has requested a loan of {loan_amount} rupees. Do you want to give him the loan? "

    # for member_id in members:
    #     if member_id != sender_id:
    bot.send_message(sender_id, notification_msg)


# create group

#mapping
mappings = {
    'greetings': send_greet,
    'borrow_loan': borrow_loan,
    'borrow_amount': process_loan_request,
    'bye': bye,
    'loan_notification': send_loan_notification,
    None: default_handler
}

# training model
assistant = GenericAssistant(
    'src/intents.json', mappings, "peer_to_peer_lending_bot")

assistant.train_model()
assistant.save_model()


bot.polling()
