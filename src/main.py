import telebot
from neural_intents import GenericAssistant
import sys
from database import *
from poll import create_poll
import re
API_KEY = '6410553908:AAFPXhYc8Yh0jcs-w_U1qIpuYI2RCkKSCHA'

bot = telebot.TeleBot(API_KEY, parse_mode=None)


@bot.message_handler(commands=["start", "hello"])
def send_hello_message(msg):
    bot.reply_to(msg, "Hello! This is a peer-to-peer lending bot!")

@bot.message_handler(commands=["join_group"])
def initiate_add_to_group_request(msg):
    add_to_group_request(msg)

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
def extract_numeric_value(sentence):
    matches = re.findall(r'\b\d+\b', sentence)
    
    if matches:
        return float(matches[0])
    else:
        return None


def bye(msg):
    bot.send_message(msg.chat.id, "Goodbye!")
    bot.stop_polling()
    sys.exit(0)

def thanks(msg):
    bot.send_message(msg.chat.id, "You're welcome:)")


def default_handler(msg):
    bot.reply_to(msg, "I did not understand.")


# loan notification
def borrow_loan(msg):
    user_id = msg.from_user.id
    group_id= msg.chat.id
    username = msg.from_user.username
    if group_id == None:
        bot.send_message(user_id, "You are not a part of a group. Please create/join a group")
    if username is None:
        bot.send_message(user_id, "Please set your Telegram username before interacting with this bot.")
        return
    loan_msg = bot.reply_to(msg, "How much money do you want to borrow?")
    bot.register_next_step_handler(loan_msg, lambda msg: process_loan_request(msg, user_id, group_id))


def process_loan_request(msg, user_id, group_id):
    loan_amount = extract_numeric_value(msg.text)

    if loan_amount is not None:
        response = f"Your loan request of {loan_amount} rupees is under process. You will be informed within 30 minutes."
        bot.reply_to(msg, response)
        create_poll(msg)
    else:
        bot.reply_to(msg, "Invalid amount. Please enter a numeric value greater than zero.")
        borrow_loan(msg)

def send_loan_notification(group_id, sender_id, loan_amount):
    # members = get_group_members(group_id)
    notification_msg = f"User {sender_id} has requested a loan of {loan_amount} rupees. Do you want to give him the loan? "

    # for member_id in members:
    #     if member_id != sender_id:
    bot.send_message(sender_id, notification_msg)


# create group
def create_group(msg):
    user_id = msg.from_user.id
    username = msg.from_user.username
    if username is None:
        bot.send_message(user_id, "Please set your Telegram username before interacting with this bot.")
        return
    group_name_msg = bot.reply_to(msg, "Please enter the group name. Please keep in mind that name is case sensitive.")
    bot.register_next_step_handler(group_name_msg, lambda msg: process_group_name(msg, user_id))

def process_group_name(msg, user_id):
    group_name = msg.text
    if(is_group_exists(group_name)):
        bot.send_message(user_id, f"Group '{group_name}' already exists. Please choose another name.")
        return create_group(msg)
    join_code_msg = bot.send_message(user_id, "Please enter the join code for the group that you want to create. This code will be used by others to join the group.")
    bot.register_next_step_handler(join_code_msg, lambda msg: process_join_code(msg, user_id, group_name))

def process_join_code(msg, user_id, group_name):
    join_code = msg.text
    password_msg = bot.send_message(user_id, "Please enter admin password for the group. This password will be used by you to login as admin of this group.")
    bot.register_next_step_handler(password_msg, lambda msg: process_password(msg, user_id, group_name, join_code))

def process_password(msg, user_id, group_name, join_code):
    username = msg.from_user.username
    password = msg.text
    group_creation(group_name, user_id, password,join_code , username) 
    bot.send_message(user_id, f"Group '{group_name}' created successfully with join code: {join_code} and you are the admin for that group")


# join group 
def add_to_group_request(msg):
    user_id = msg.from_user.id
    username = msg.from_user.username
    if username is None:
        bot.send_message(user_id, "Please set your Telegram username before interacting with this bot.You will be known by that username in the group. So please set it accordingly.")
        return
    else:
        bot.send_message(user_id, "Please enter the name of the group you want to join. Please keep in mind that name is case sensitive.")
        bot.register_next_step_handler(msg, lambda msg: process_group_name_for_join(msg, user_id, username))

def process_group_name_for_join(msg, user_id, username):
    group_name = msg.text
    if is_group_exists(group_name):
        bot.send_message(user_id, "Please enter the join code for the group. If you don't have it ask admin for the join code.")
        bot.register_next_step_handler(msg, lambda msg: process_join_code_for_join(msg, user_id, username, group_name))
    else:
        bot.send_message(user_id, f"Group '{group_name}' does not exist.")
        return add_to_group_request(msg)

def process_join_code_for_join(msg, user_id, username, group_name):
    join_code = msg.text
    if is_join_code_correct(group_name, join_code):
        send_request_to_admin(group_name, user_id, username)
        bot.send_message(user_id, "Your request has been sent to the admin. You will be notified once the admin acknowledges your request.")
    else:
        bot.send_message(user_id, "Incorrect join code. Please try again.")
        return add_to_group_request(msg)
        

def send_request_to_admin(group_name, user_id, username):
    admin_id = get_admin_id(group_name)
    if admin_id is not None:
        notification_msg = f"User @{username} wants to join the group '{group_name}'. Do you approve?"  
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add("Yes", "No")
        bot.send_message(admin_id, notification_msg, reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(admin_id, lambda msg: process_admin_response(msg, group_name, user_id, username))

def process_admin_response(msg, group_name, user_id, username):
    admin_response = msg.text.lower()
    if admin_response == "yes":
        if add_member(group_name, user_id,username):
            bot.send_message(user_id, f"Congratulations! You have been added to the group '{group_name}'.")
        else:
            bot.send_message(user_id, "You are already a member of this group.")
    elif admin_response == "no":
        bot.send_message(user_id, f"Your request to join the group '{group_name}' has been rejected by the admin.")
    else:
        bot.send_message(user_id, "Invalid response. Please select 'Yes' or 'No'.")

#mapping
mappings = {
    'greetings': send_greet,
    'borrow_loan': borrow_loan,
    'borrow_amount': process_loan_request,
    'bye': bye,
    'create_group': create_group,  
    'join_group': initiate_add_to_group_request,
    None: default_handler
}

assistant = GenericAssistant(
    'src/intents.json', mappings, "peer_to_peer_lending_bot")

assistant.train_model()
assistant.save_model()


bot.infinity_polling()
