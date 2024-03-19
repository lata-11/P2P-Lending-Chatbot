import telebot
from neural_intents import GenericAssistant
import sys
sys.stdout.reconfigure(encoding='utf-8')

from database import *
import re
API_KEY = '6410553908:AAFPXhYc8Yh0jcs-w_U1qIpuYI2RCkKSCHA'

bot = telebot.TeleBot(API_KEY, parse_mode=None)


@bot.message_handler(commands=["start", "hello"])
def send_hello_message(msg):
    bot.reply_to(msg, "Hello! This is a peer-to-peer lending bot!")

@bot.message_handler(commands=["join_group"])
def initiate_add_to_group_request(msg):
    add_to_group_request(msg)
    
@bot.message_handler(commands=["create_group"])
def initiate_create_group_request(msg):
    create_group(msg)
        
@bot.message_handler(commands=["delete_group"])
def initiate_delete_group_request(msg):
    delete_group_request(msg)
    
@bot.message_handler(commands=["borrow_loan"])
def initiate_loan_process(msg):
    get_member_groups(msg)
 
@bot.message_handler(commands=["show_group_members"])
def initiate_show_group_members_request(msg):
    show_group_members_request(msg)

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

def bye(msg):
    bot.send_message(msg.chat.id, "Goodbye!")
    bot.stop_polling()
    sys.exit(0)

def thanks(msg):
    bot.send_message(msg.chat.id, "You're welcome:)")


def default_handler(msg):
    bot.reply_to(msg, "I did not understand.")


# borrow loan
def extract_numeric_value(sentence):
    matches = re.findall(r'\b\d+\b', sentence)
    
    if matches:
        return float(matches[0])
    else:
        return None

def get_member_groups(msg):
    user_id=msg.from_user.id
    username=msg.from_user.username
    if username is None:
        bot.send_message(user_id, "Please set your Telegram username before interacting with this bot.")
        return
    member_groups = get_groups_of_member(user_id)
    
    if not member_groups:
        bot.send_message(user_id, "You are not a part of any group. Please create or join a group to proceed.")
        return
    else:
        group_list = [{"name": group} for group in member_groups]
        group_display = "\n".join([f"{i+1}. {group['name']}" for i, group in enumerate(group_list)])
        
        bot.send_message(user_id, "You are a member of the following groups:\n" + group_display)
        bot.send_message(user_id, "Please choose the group from which you want to borrow money by entering the corresponding number:")
        bot.register_next_step_handler(msg, process_group_selection, user_id, group_list)

def process_group_selection(msg, user_id, member_groups):
    try:
        choice = int(msg.text)
        if choice < 1 or choice > len(member_groups):
            bot.send_message(user_id, "Invalid choice. Please enter a valid group number.")
            bot.register_next_step_handler(msg, process_group_selection, user_id, member_groups)
            return
        chosen_group = member_groups[choice - 1] 
        bot.send_message(user_id, f"You've chosen group: {chosen_group['name']}")
        group_id=get_group_id(chosen_group['name'])
        borrow_loan(msg, group_id)
    except ValueError:
        bot.send_message(user_id, "Invalid input. Please enter a number.")

def borrow_loan(msg,group_id):
    user_id = msg.from_user.id
    if group_id == None:
        bot.send_message(user_id, "Invalid group id. Please enter a valid group")
    loan_msg = bot.reply_to(msg, "How much money do you want to borrow?")
    bot.register_next_step_handler(loan_msg, lambda msg: process_loan_request(msg, user_id, group_id))


def process_loan_request(msg, user_id, group_id):
    loan_amount = (extract_numeric_value(msg.text))
    username = msg.from_user.username

    if loan_amount is not None:
        response = f"Your loan request of {loan_amount} rupees is under process. You will be informed within 30 minutes."
        bot.reply_to(msg, response)
        create_poll(msg, user_id, username,loan_amount, group_id)
    else:
        bot.reply_to(msg, "Invalid amount. Please enter a numeric value greater than zero.")
        borrow_loan(msg)

#create poll
def create_poll(msg, user_id, username, loan_amount, group_id):
    sent_msg =f"A group member of yours has requested a loan of {loan_amount}. Are you willing to give?"
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add("Yes", "No")
    bot.send_message(user_id,sent_msg, reply_markup=markup) 
    bot.register_next_step_handler_by_chat_id(user_id, lambda msg: handle_poll_response(msg,group_id, loan_amount, user_id, username))

def handle_poll_response(msg, group_id, loan_amount, user_id, username):
    user_response = msg.text.lower()
    upi_id = get_upi_id(username)  
    if user_response == "yes":
        bot.send_message(user_id, "You voted 'Yes'! Thank you for lending.")
        get_proposal(msg, user_id, group_id, loan_amount)
        #send_upi_details(user_id, upi_id)
    elif user_response == "no":
        bot.send_message(user_id, "You voted 'No'!")

#proposal    
def get_proposal(msg, user_id, group_id, loan_amount):
    send_msg = f"Hi, Please provide the interest rate/day for the loan of {loan_amount}"
    bot.send_message(user_id, send_msg)
    
    def process_next_step(msg):
        process_interest_rate(msg, group_id, user_id)

    bot.register_next_step_handler(msg, process_next_step)

def process_interest_rate(msg, group_id, user_id):
    interest_rate = msg.text
    add_proposal(user_id, group_id, interest_rate, user_id)  # 2nd user_id is borrower id
    bot.send_message(user_id, "Thanks for providing the interest rate!")
    bot.register_next_step_handler(msg, all_proposals(msg, user_id, group_id))

#show proposal to the borrower
def all_proposals(msg, user_id, group_id):
    bot.send_message(user_id, "Hi, Here are the proposals you got for the loan you asked.")
    proposals = show_proposals(group_id)
    if isinstance(proposals, str) and proposals.startswith("Error occurred"):
        bot.send_message(user_id, proposals)
    elif proposals == "No proposals found.":
        bot.send_message(user_id, proposals)
    else:
        for i, interest_rate in enumerate(proposals, start=1):
            bot.send_message(user_id, f"{i}. Interest Rate/day: {interest_rate}")
        bot.send_message(user_id, "Please choose a proposal by entering the corresponding number.")
        bot.register_next_step_handler(msg, choose_proposal, user_id, group_id, proposals)

#choose a proposal
def choose_proposal(msg, user_id, group_id, proposals):
    try:
        choice = int(msg.text)
        if choice < 1 or choice > len(proposals):
            bot.send_message(user_id, "Invalid choice. Please enter a valid proposal number.")
            bot.register_next_step_handler(msg, choose_proposal, user_id, group_id, proposals)
            return
        chosen_proposal = proposals[choice - 1]  # Adjust index to zero-based
        bot.send_message(user_id, f"You've chosen proposal {choice}. Interest Rate/day: {chosen_proposal}")
        # Process further if needed
    except ValueError:
        bot.send_message(user_id, "Invalid input. Please enter a number.")
        bot.register_next_step_handler(msg, choose_proposal, user_id, group_id, proposals)
        
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
        bot.send_message(user_id, "Please provide your UPI ID that you'll use for lending/receiving a loan.")
        # Register a handler to capture UPI ID
        bot.register_next_step_handler(msg, lambda msg: process_upi_id(msg, group_name, user_id, username))
    elif admin_response == "no":
        bot.send_message(user_id, f"Your request to join the group '{group_name}' has been rejected by the admin.")
    else:
        bot.send_message(user_id, "Invalid response. Please select 'Yes' or 'No'.")

def process_upi_id(msg, group_name, user_id, username):
    upi_id = msg.text
    bot.send_message(user_id, "Thank you for providing your UPI ID.")
    
    bot.send_message(user_id, "Please provide your phone number linked to your UPI ID.")
    # Register a handler to capture phone number
    bot.register_next_step_handler(msg, lambda msg: process_phone_number(msg, group_name, user_id, username, upi_id))

def process_phone_number(msg, group_name, user_id, username, upi_id):
    phone_number = msg.text
    bot.send_message(user_id, "Thank you for providing your phone number.")
    
    add_member(group_name, user_id, username, upi_id, phone_number)
    
    bot.send_message(user_id, f"Congratulations! You have been added to the group '{group_name}'.")
    

# remove from group

def leave_group_request(msg):
    user_id=msg.from_user.id
    username=msg.from_user.username
    if username is None:
        bot.send_message(user_id,"Please set your Telegram username before interacting with this bot.You will be known by that username in the group. So please set it accordingly.")
        return
    else:
        bot.send_message(user_id, "Please enter the name of the group you want to exit. Please keep in mind that name is case sensitive.")
        bot.register_next_step_handler(msg, lambda msg: process_group_name_for_removal(msg, user_id, username))

def process_group_name_for_removal(msg, user_id, username):
    group_name = msg.text
    if is_group_exists(group_name):
        bot.register_next_step_handler(msg, lambda msg: process_removal_request(msg, user_id, username, group_name))
    else:
        bot.send_message(user_id, f"Group '{group_name}' does not exist.")
        return leave_group_request(msg)
    
def process_removal_request(msg, user_id, username,group_name):
    if(leave_group(username,user_id,group_name)):
        bot.send_message(user_id,f"You have been removed from the group '{group_name}' ,Successfully.")
    else:
        bot.send_message(user_id,"Invalid request. You are not the member of this group.")

# get upi id
def send_upi_details(user_id, upi_id):
    send_msg= f"Hi, you wished to lend a loan. Here are the details. UPI ID: {upi_id}"
    bot.send_message(user_id, send_msg)
    
#delete_group
def delete_group_request(msg):
    user_id = msg.from_user.id
    username = msg.from_user.username
    if username is None:
        bot.send_message(user_id, "Please set your Telegram username before interacting with this bot.")
        return
    bot.send_message(user_id, "Please enter the name of the group you want to delete:")
    bot.register_next_step_handler(msg, lambda msg: process_delete_group_name(msg, user_id))

def process_delete_group_name(msg, user_id):
    group_name = msg.text
    if(is_group_exists(group_name)):
        admin_id = get_admin_id(group_name)
        if admin_id == user_id:
            bot.send_message(user_id, f"Please enter the admin password for the group '{group_name}':")
            bot.register_next_step_handler(msg, lambda msg: process_delete_group_password(msg, group_name))
        else:
            bot.send_message(user_id, "You are not the admin of this group. You cannot delete it.")
    else:
        bot.send_message(user_id, f"Group '{group_name}' does not exist.")

def process_delete_group_password(msg, group_name):
    admin_password = msg.text
    user_id = msg.from_user.id
    result = delete_group(group_name, admin_password)
    bot.send_message(user_id, result)

#show group members
def show_group_members_request(msg):
    user_id = msg.from_user.id
    send_msg = "Sure! Please provide the name of the group you want to view members for."
    bot.send_message(user_id, send_msg)
    bot.register_next_step_handler(msg, lambda msg: process_group_name_for_display_members(msg, user_id))

def process_group_name_for_display_members(msg, user_id):
    group_name = msg.text
    if is_group_exists(group_name):
        admin_id = get_admin_id(group_name)
        if admin_id == user_id:
            bot.send_message(user_id, f"Please enter the admin password for the group '{group_name}':")
            bot.register_next_step_handler(msg, lambda msg: process_display_members_password(msg, group_name))
        else:
            bot.send_message(user_id, "You are not the admin of this group. Only admins can view the members.")
    else:
        bot.send_message(user_id, f"Group '{group_name}' does not exist.")

def process_display_members_password(msg, group_name):
    admin_password = msg.text
    user_id = msg.from_user.id
    if not admin_login(user_id, admin_password, group_name):
        bot.send_message(user_id, "Incorrect admin password. Access denied.")
        return
    members = get_group_members(group_name)
    if members:
        member_list = "\n".join([f"@{member['Member_name']}" for member in members])
        bot.send_message(user_id, f"Members of group '{group_name}':\n{member_list}")
    else:
        bot.send_message(user_id, f"No members found in group '{group_name}'.")

#show groups
def show_member_groups(msg):
    user_id = msg.from_user.id
    username = msg.from_user.username
    if username is None:
        bot.send_message(user_id, "Please set your Telegram username before interacting with this bot.")
        return
    member_groups = get_groups_of_member(user_id)
    if not member_groups:
        bot.send_message(user_id, "You are not a part of any group. Please create or join a group to proceed.")
        return
    else:
        group_list = [{"name": group} for group in member_groups]
        group_display = "\n".join([f"{i+1}. {group['name']}" for i, group in enumerate(group_list)])
        bot.send_message(user_id, "You are a member of the following groups:\n" + group_display)

#mapping
mappings = {
    'greetings': send_greet,
    'borrow_loan': initiate_loan_process ,
    'borrow_amount': process_loan_request,
    'bye': bye,
    'create_group': initiate_create_group_request,
    'join_group': initiate_add_to_group_request,
    'delete_group': initiate_delete_group_request,
    'leave_group':leave_group_request,
    'show_group_members': initiate_show_group_members_request,
    'show_member_groups': show_member_groups,  
    None: default_handler
}

assistant = GenericAssistant(
    'src/intents.json', mappings, "peer_to_peer_lending_bot")

assistant.train_model()
assistant.save_model()


bot.infinity_polling()
