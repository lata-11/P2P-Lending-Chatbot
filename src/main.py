import telebot
from neural_intents import GenericAssistant
import sys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import matplotlib.pyplot as plt
from dotenv import load_dotenv
sys.stdout.reconfigure(encoding='utf-8')
import uuid
from database import *
import re
import threading
import os
load_dotenv()

API_KEY = os.getenv("TELE_API_KEY")
bot = telebot.TeleBot(API_KEY, parse_mode=None)

respond_time = os.getenv("RESPOND_TIME")

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
    borrower_id = msg.from_user.id
    if group_id == None:
        bot.send_message(borrower_id, "Invalid group id. Please enter a valid group")
        bot.register_next_step_handler(msg, lambda msg: get_member_groups(msg)) 
    loan_msg = bot.reply_to(msg, "How much money do you want to borrow?")
    bot.register_next_step_handler(loan_msg, lambda msg: process_loan_request(msg, borrower_id, group_id))

def process_loan_request(msg, borrower_id, group_id):
    loan_amount = (extract_numeric_value(msg.text))
    username = msg.from_user.username
    message_time = msg.date

    if loan_amount is not None:
        response = f"Your loan request of {loan_amount} rupees is under process. You will be informed within 30 minutes."
        bot.reply_to(msg, response)
        loan_uuid = str(uuid.uuid4()) 
        create_poll(msg, borrower_id,loan_amount, group_id,loan_uuid,message_time)
        schedule_all_proposals(borrower_id,group_id,loan_amount,loan_uuid)
    else:
        bot.reply_to(msg, "Invalid amount. Please enter a numeric value greater than zero.")
        borrow_loan(msg)

def schedule_all_proposals(borrower_id,group_id,loan_amount,loan_uuid):
    threading.Timer(0.5 * 60, all_proposals, args=(borrower_id, group_id, loan_amount,loan_uuid)).start()

#create poll
def create_poll(msg, borrower_id, loan_amount, group_id,loan_uuid,stored_timestamp):
    sent_msg = f"A group member of yours has requested a loan of {loan_amount}. Are you willing to give? Please respond with 'Yes' or 'No' within 30 minutes."
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add("Yes", "No")
    group_name=get_group_name(group_id)
    group_members = db["Members"].find({"Group_id": group_id})
    for member in group_members:
        lender_id = member["telegram_id"]
        if lender_id == borrower_id or lender_id == get_admin_id(group_name):
            continue
        else:
            bot.send_message(lender_id, sent_msg, reply_markup=markup) 
            bot.register_next_step_handler_by_chat_id(lender_id, lambda msg: handle_poll_response(msg, group_id, loan_amount, lender_id, borrower_id,loan_uuid,stored_timestamp))

def handle_poll_response(msg, group_id, loan_amount, user_id,borrower_id,loan_uuid,stored_timestamp):
    lender_id=msg.from_user.id
    response = msg.text.strip().lower()
    message_time = msg.date
    time_difference = message_time - stored_timestamp

    if time_difference > respond_time * 60:  #later will change to 30 mins or any time
        bot.send_message(lender_id, "The time limit to propose a proposal has exceeded. You cannot propose propsal for this loan now.")
        return
    
    if response == "yes":
        bot.send_message(lender_id, f"Thank you for your willingness to lend {loan_amount}.")
        send_msg = f"Hi, Please provide the interest rate/day for the loan of {loan_amount}"
        bot.send_message(lender_id, send_msg)
        bot.register_next_step_handler_by_chat_id(lender_id, lambda msg:process_interest_rate(msg, group_id, lender_id, loan_amount,borrower_id,loan_uuid,stored_timestamp)) 
    elif response == "no":
        bot.send_message(user_id, "Thank you for your response.")
    else:
        bot.send_message(user_id, "Invalid response. Please select 'Yes' or 'No'.")
        return handle_poll_response(msg, group_id, loan_amount, lender_id, borrower_id)

def process_interest_rate(msg, group_id, user_id, loan_amount, borrower_id,loan_uuid,stored_timestamp):
    interest_rate = msg.text
    message_time = msg.date
    time_difference = message_time - stored_timestamp

    if time_difference >respond_time * 60:  #later will change to 30 mins or any time
        bot.send_message(lender_id, "The time limit to propose a proposal has exceeded. You cannot propose propsal for this loan now.")
        return
    lender_id=msg.from_user.id
    add_proposal(lender_id, group_id, interest_rate, loan_amount, borrower_id,loan_uuid)
    bot.send_message(lender_id, "Thanks for providing the interest rate!")
    
def all_proposals(borrower_id, group_id, loan_amount, loan_uuid):
    bot.send_message(borrower_id, "Hi, Here are the proposals you got for the loan you asked.")
    proposals = show_proposals(loan_uuid)
    print(loan_uuid)
    if isinstance(proposals, str) and proposals.startswith("Error occurred"):
        bot.send_message(borrower_id, proposals)
    elif proposals == "No proposals found.":
        bot.send_message(borrower_id, proposals)
    else:
        proposal_messages = [f"{i}. Interest Rate/day: {proposal['interest']}" for i, proposal in enumerate(proposals, start=1)]
        proposals_display = "\n".join(proposal_messages)
        bot.send_message(borrower_id, proposals_display)
        bot.send_message(borrower_id, "Please choose a proposal by entering the corresponding number.")
        bot.register_next_step_handler_by_chat_id(borrower_id, lambda msg: choose_proposal(msg, borrower_id, group_id, loan_amount, proposals))

def choose_proposal(msg, user_id, group_id, loan_amount, proposals):
    try:
        choice = int(msg.text)
        if choice < 1 or choice > len(proposals):
            bot.send_message(user_id, "Invalid choice. Please enter a valid proposal number.")
            bot.register_next_step_handler(msg, choose_proposal, user_id, group_id, loan_amount, proposals)
            return
        chosen_proposal = proposals[choice - 1]  
        lender_id = chosen_proposal["lender_id"]  # Assuming lender_id is present in the proposal
        bot.send_message(user_id, f"You've chosen proposal {choice}. Interest Rate/day: {chosen_proposal['interest']}. Please wait we are transferring the amount to your UPI ID.")
        return_time = get_group_repay_time(group_id)
        add_transaction(user_id, lender_id, group_id, loan_amount, chosen_proposal["interest"],return_time)
        send_admin_upi_details(chosen_proposal)
    except ValueError:
        bot.send_message(user_id, "Invalid input. Please enter a number.")
        bot.register_next_step_handler(msg, choose_proposal, user_id, group_id, loan_amount, proposals)

def send_admin_upi_details(chosen_proposal):
    user_id=chosen_proposal["lender_id"]
    group_id=chosen_proposal["group_id"]
    loan_amount=chosen_proposal["loan_amount"]
    group_name = get_group_name(group_id)
    admin_upi_id = get_admin_upi_id(group_name)
    admin_id=get_admin_id(group_name)
    borrower_username = get_member_name(chosen_proposal["borrower_id"])
    lender_username = get_member_name(user_id)
    if admin_upi_id:
        send_msg = f"Hi, Your proposal has been accepted by the borrrower. Please send the loan amount of {loan_amount} to admin's UPI ID{admin_upi_id}."
        bot.send_message(user_id, send_msg)
        bot.send_message(admin_id, f"Hi, A member @{borrower_username} of group {group_name} has accepted the proposal of @{lender_username} for loan just now. You will have to get involved in the transaction. Please stay active for some time.")
        lender_confirmation(chosen_proposal)
    else:
        print("Admin ID not found for group:", group_name)

def lender_confirmation(chosen_proposal):
    user_id=chosen_proposal["lender_id"]
    loan_amount=chosen_proposal["loan_amount"]
    lender_response_text = f"Have you sent the loan amount of {loan_amount} to the admin? Please reply in 'Yes' or 'No'."
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add("Yes", "No")
    lender_response_msg = bot.send_message(user_id, lender_response_text, reply_markup=markup) 
    bot.register_next_step_handler_by_chat_id(user_id, lambda msg: handle_lender_response(msg, chosen_proposal))
    
def handle_lender_response(msg, chosen_proposal):
    group_name=get_group_name(chosen_proposal["group_id"])
    admin_id=get_admin_id(group_name)
    response = msg.text.strip().lower()
    lender_id=chosen_proposal["lender_id"]
    loan_amount=chosen_proposal["loan_amount"]
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add("Yes", "No")
    if response == "yes":
        bot.send_message(lender_id, f"Great! I will inform the admin.")
        bot.send_message(admin_id, f"Hi, The lender has sent the loan amount of {loan_amount}. Please confirm if you have received the money by typing 'Yes' or 'No'.",reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(admin_id, lambda msg: handle_admin_recieved_payment(msg, chosen_proposal))
    elif response == "no":
        bot.send_message(lender_id, "No problem! I will inform the admin.")
        bot.send_message(admin_id, f"Hi, The lender has not sent the loan amount of {loan_amount}. He may have cancelled the loan. Please contact him personally")
    else:
        bot.send_message(len, "Invalid response. Please select 'Yes' or 'No'.")
        
def handle_admin_recieved_payment(msg, chosen_proposal):
    response = msg.text.strip().lower()
    user_id=chosen_proposal["borrower_id"]
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add("Yes", "No")
    if response == "yes":
        send_upi_details(chosen_proposal)
    elif response == "no":
        bot.send_message(user_id, "No problem! I will inform the lender.")
        return lender_confirmation(chosen_proposal)
    else:
        bot.send_message(user_id, "Invalid response. Please select 'Yes' or 'No'.",markup=markup)
        return bot.register_next_step_handler_by_chat_id(user_id, lambda msg: handle_admin_recieved_payment(msg, chosen_proposal))

def send_upi_details(chosen_proposal):
    user_id=chosen_proposal["borrower_id"]
    loan_amount=chosen_proposal["loan_amount"]
    group_name=get_group_name(chosen_proposal["group_id"])
    admin_id=get_admin_id(group_name)
    member_name=get_member_name(user_id)
    upi_id=get_upi_id(member_name)
    send_msg = f"Please send them the money you recently received. Here are the details. UPI ID: {upi_id}"
    bot.send_message(admin_id, send_msg) 
    admin_confirmation(chosen_proposal)
    
# ask confirmation of admin whether they did payment or not
def admin_confirmation(chosen_proposal):
    group_name=get_group_name(chosen_proposal["group_id"])
    admin_id=get_admin_id(group_name)
    loan_amount=chosen_proposal["loan_amount"]
    member_name=get_member_name(chosen_proposal["borrower_id"])
    admin_response_text = f"Have you made the payment of {loan_amount} to {member_name}? Please reply in 'Yes' or 'No'."
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add("Yes", "No")
    admin_response_msg = bot.send_message(admin_id, admin_response_text, reply_markup=markup) 
    bot.register_next_step_handler_by_chat_id(admin_id, lambda msg: handle_admin_response(msg, chosen_proposal))

    
def handle_admin_response(msg, chosen_proposal):
    response = msg.text.strip().lower()
    group_name=get_group_name(chosen_proposal["group_id"])
    borrower_name=get_member_name(chosen_proposal["borrower_id"])
    admin_id=get_admin_id(group_name)
    if response == "yes":
        bot.send_message(admin_id, f"Great! I will inform {borrower_name}.")
        borrower_confirmation(chosen_proposal)
    elif response == "no":
        bot.send_message(admin_id, "No problem! I will inform them.")
    else:
        bot.send_message(admin_id, "Invalid response. Please select 'Yes' or 'No'.")
        return admin_confirmation(chosen_proposal)
        
def borrower_confirmation(chosen_proposal):
    loan_amount=chosen_proposal["loan_amount"]
    user_id=chosen_proposal["borrower_id"]
    borrower_response_text = f"Have you recieved the payment of {loan_amount}? Please reply in 'Yes' or 'No'."
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add("Yes", "No")
    bot.send_message(user_id, borrower_response_text, reply_markup=markup) 
    bot.register_next_step_handler_by_chat_id(user_id, lambda msg: handle_borrower_response(msg, chosen_proposal))

    
def handle_borrower_response(msg,chosen_proposal):
    borrower_id=chosen_proposal["borrower_id"]
    response = msg.text.strip().lower()
    group_name=get_group_name(chosen_proposal["group_id"])
    if response == "yes":
        bot.send_message(borrower_id, f"Great! Thank you for your confirmation.")
        send_repay_details(chosen_proposal)
    elif response == "no":
        bot.send_message(borrower_id, "Let me confirm then I ll let you know.")
        return admin_confirmation(chosen_proposal)
    else:
        bot.send_message(borrower_id, "Invalid response. Please select 'Yes' or 'No'.")


def draw_pie_charts(c, loan_amount, interest_rate, repayment_amount):
    labels = ['Loan Amount', 'Interest Rate']
    sizes = [loan_amount, interest_rate]

    plt.figure(figsize=(8, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal') 

    plt.savefig('pie_chart1.png', format='png', bbox_inches='tight')
    plt.close()  
    c.drawImage('pie_chart1.png', 120, 450, width=300, height=200)

    labels = ['Loan Amount', 'Extra repayment amount']
    sizes = [loan_amount, repayment_amount]

    plt.figure(figsize=(8, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal') 

    plt.savefig('pie_chart2.png', format='png', bbox_inches='tight')
    plt.close()  
    c.drawImage('pie_chart2.png', 120, 150, width=300, height=200)

def send_repay_details(chosen_proposal):
    user_id=chosen_proposal["borrower_id"]
    loan_amount=chosen_proposal["loan_amount"]
    group_name=get_group_name(chosen_proposal["group_id"])
    admin_id=get_admin_id(group_name)
    # Create a PDF file
    filename = f"repayment_details_{user_id}.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    
    transaction_collections = db["Transaction"]
    transaction = transaction_collections.find_one(
        {"Borrower_id": user_id},
        sort=[("transaction_date", -1)]  
    )
    group_collections = db["Groups"]
    group = group_collections.find_one({"name": group_name})
    repay_time = group.get("repay_time")
    if repay_time:
       repay_time = float(repay_time)
    else:
        repay_time = 1
    
    if transaction:
        interest_rate = transaction["interest"]
        loan_amount= float(loan_amount)
        interest_rate= float(interest_rate)
        repayment_amount = loan_amount + (loan_amount + interest_rate) * repay_time
        
        c.drawString(100, 750, "Please find your repayment details in this invoice.")
        c.drawString(100, 730, f"Loan amount: ${loan_amount}")
        c.drawString(100, 710, f"Interest rate per day: {interest_rate}%")
        c.drawString(100, 690, f"Repay time: {repay_time}")
        c.drawString(100, 670, f"Repayment amount: ${repayment_amount}")
        
        draw_pie_charts(c, loan_amount, interest_rate, repayment_amount-loan_amount)
        
        c.save()
        
        with open(filename, "rb") as file:
            bot.send_document(user_id, file)
    else:
        print("No transaction found for the user ID:", user_id)


#create group   
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
    if is_group_exists(group_name):
        bot.send_message(user_id, f"Group '{group_name}' already exists. Please choose another name.")
        create_group(msg)
        return
    join_code_msg = bot.send_message(user_id, "Please enter the join code for the group that you want to create. This code will be used by others to join the group.")
    bot.register_next_step_handler(join_code_msg, lambda msg: process_join_code(msg, user_id, group_name))

def process_join_code(msg, user_id, group_name):
    join_code = msg.text
    password_msg = bot.send_message(user_id, "Please enter admin password for the group. This password will be used by you to login as admin of this group.")
    bot.register_next_step_handler(password_msg, lambda msg: process_password(msg, user_id, group_name, join_code))

def process_password(msg, user_id, group_name, join_code):
    admin_password = msg.text
    upi_id_msg = bot.send_message(user_id, "Please enter the admin UPI ID which you'll use for this group.")
    bot.register_next_step_handler(upi_id_msg, lambda msg: process_admin_upi_id(msg, user_id, group_name, join_code, admin_password))

def process_admin_upi_id(msg, user_id, group_name, join_code, admin_password):
    upi_id = msg.text 
    repay_time = bot.send_message(user_id, "Please enter the repay duration in days for this group.")
    bot.register_next_step_handler(repay_time, lambda msg: process_repay_duration(msg, user_id, group_name, join_code, admin_password, upi_id))

def process_repay_duration(msg, user_id, group_name, join_code, admin_password, upi_id):
    repay_time=msg.text
    username = msg.from_user.username
    group_creation(group_name, user_id, admin_password, join_code, username, upi_id, repay_time) 
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
        group_id = get_group_id(group_name)
        if(already_member_of_group(user_id,group_id)):
            bot.send_message(user_id, "You are already member of this group.")
            return
        bot.send_message(user_id, "Please enter the join code for the group. If you don't have it ask admin for the join code.")
        bot.register_next_step_handler(msg, lambda msg: process_join_code_for_join(msg, user_id, username, group_name))
    else:
        bot.send_message(user_id, f"Group '{group_name}' does not exist.")
        return 

def process_join_code_for_join(msg, user_id, username, group_name):
    join_code = msg.text
    if is_join_code_correct(group_name, join_code):
        bot.send_message(user_id, "Your request has been sent to the admin. You will be notified once the admin acknowledges your request.")
        admin_id = get_admin_id(group_name)
        if admin_id is not None:
            notification_msg = f"User @{username} wants to join the group '{group_name}'. Do you approve?"  
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add("Yes", "No")
            bot.send_message(admin_id, notification_msg, reply_markup=markup)
            bot.register_next_step_handler_by_chat_id(admin_id, lambda msg: process_admin_response(msg, group_name, user_id, username))
    else:
        bot.send_message(user_id, "Incorrect join code. Please try again.")
        return add_to_group_request(msg)
        
def process_admin_response(msg, group_name, user_id, username):
    admin_response = msg.text.lower()
    if admin_response == "yes":
        group_id=get_group_id(group_name)
        if(member_exists(user_id)==False):
            bot.send_message(user_id, "Please provide your UPI ID that you'll use for lending/receiving a loan..")
            bot.register_next_step_handler_by_chat_id(user_id, lambda msg: process_upi_id(msg, group_name, user_id, username))
        else:
            add_old_member(user_id,group_id)
            bot.send_message(user_id, f"Your request to join has been accepted by admin. Congratulations! You have been added to the group '{group_name}'.")
    elif admin_response == "no":
        bot.send_message(user_id, f"Your request to join the group '{group_name}' has been rejected by the admin.")
    else:
        bot.send_message(user_id, "Invalid response. Please select 'Yes' or 'No'.")

def process_upi_id(msg, group_name, user_id, username):
    upi_id = msg.text
    bot.send_message(user_id, "Thank you for providing your UPI ID.")
    bot.send_message(user_id, "Please provide your phone number linked to your UPI ID.")
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


bot.polling(non_stop=True)