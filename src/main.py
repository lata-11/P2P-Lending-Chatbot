import telebot
API_KEY='6410553908:AAFPXhYc8Yh0jcs-w_U1qIpuYI2RCkKSCHA'

bot = telebot.TeleBot(API_KEY, parse_mode=None)


@bot.message_handler(commands=["start", "hello"])
def send_hello_message(msg):
    bot.reply_to(msg, "Hello! This is a peer-to-peer lending bot!")

# borrow loan


@bot.message_handler(commands=["loan", "borrow"])
def borrow_loan(msg):
    loan_amount = bot.reply_to(msg, "How much do you want to borrow?")
    bot.register_next_step_handler(loan_amount, waiting_time)

def waiting_time(msg):
    waiting_time = bot.reply_to(msg, "How many hours are you willing to wait for me to find a lender?")
    bot.register_next_step_handler(waiting_time, waiting_time_handler)
    
def waiting_time_handler(msg):
    waiting_time=msg.text 
    bot.reply_to(
        msg, f"Ok! I will try to find a lender within {waiting_time} hours.")

def borrow_loan_amount_handler(msg):
    loan_amount = msg.text
    bot.reply_to(
        msg, f"Your loan request of {loan_amount} rupees is under process.")
    

#send notification


bot.polling()
