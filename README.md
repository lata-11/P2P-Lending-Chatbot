# P2P Lending Bot

## Peer-to-Peer Lending Telegram Bot:

This Telegram bot facilitates peer-to-peer lending, allowing users to create, join, and manage lending groups, as well as request and lend money within those groups.

## Features:

- **Group Management:** Users can create, join, and delete lending groups.
- **Loan Requests:** Members can request loans from other group members.
- **Loan Proposals:** Group members can propose loan offers with interest rates.
- **Group Membership:** Users can view members of a group they're part of.
- **User Authentication:** Basic user authentication is implemented using Telegram usernames.
- **Interaction:** The bot responds to commands and prompts from users.

## Libraries Used:

- **telebot:** Python framework for Telegram Bot API.
- **neural_intents:** Library for building and managing intent-based chatbots.
- **pymongo:** Python driver for MongoDB, used for database operations.
- **re:** Regular expression operations for extracting numeric values from text.

## Setup

1. **Create Bot** by using command '/newbot' in BotFather telegram
2. **Obtain API Key:** Obtain its Telegram Bot API key from BotFather and replace `API_KEY` in the code with your own key.
3. **Install Dependencies:** Install required Python libraries using `pip install -r requirements.txt`.
4. **Database Configuration:** Set up a MongoDB database and configure connection details in the `database.py` file.
5. **Run the Bot:** Execute the Python script to run the Telegram bot.

## Usage

Start the bot by sending the `/start` command.  
Two types of login:

### Admin Login
1. Creates a Group by providing group name and group join code
2. Sets a password for admin login
3. Has access to the details of all transactions
4. Can remove a member from group
5. Can delete a group
   
### Member Login
1. Joins a group using the group name and join code provided by the admin
2. Can demand the bot for loan (no restriction on loan amount)
3. Can choose among the proposals given by the anonymous lenders
4. Repay the amount back to lender through admin

![image](https://github.com/lata-11/P2P-Lending-Chatbot/assets/143941227/1a615593-6b46-41bf-b232-723a84c32a82)

## Contributors

- Rizul Gupta
- Shambhavi Verma
- Anjana Gupta
- Lata Sah
- Anshika Gupta

## Acknowledgements

Special thanks to our mentor Sandeep Manthi for their guidance and support throughout the development process.
