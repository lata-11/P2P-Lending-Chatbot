# Desis_project

Peer-to-Peer Lending Telegram Bot:

This is a Telegram bot for peer-to-peer lending, allowing users to create, join, and manage lending groups, as well as request and lend money within those groups. The bot facilitates the borrowing and lending process among group members.

Features:

Group Management: Users can create, join, and delete lending groups.
Loan Requests: Members can request loans from other group members.
Loan Proposals: Group members can propose loan offers with interest rates.
Group Membership: Users can view members of a group they're part of.
User Authentication: Basic user authentication is implemented using Telegram usernames.
Interaction: The bot responds to commands and prompts from users.

Libraries Used:
telebot: Python framework for Telegram Bot API.
neural_intents: Library for building and managing intent-based chatbots.
pymongo: Python driver for MongoDB, used for database operations.
re: Regular expression operations for extracting numeric values from text.

Setup
Obtain API Key: Obtain a Telegram Bot API key from BotFather and replace API_KEY in the code with your own key.
Install Dependencies: Install required Python libraries using pip install -r requirements.txt.
Database Configuration: Set up a MongoDB database and configure connection details in the database.py file.
Run the Bot: Execute the Python script to run the Telegram bot.

Usage
Start the bot by sending the /start command.
Use commands like create group, join group, borrow loan, etc., to interact with the bot and perform actions.
Follow the bot's prompts to create or join groups, request or offer loans, and manage group activities.

Contributors
Rizul Gupta
Shambhavi Verma
Anjana Gupta
Lata Sah
Anshika Gupta

Acknowledgements
Special thanks to our mentor Sandeep Manthi for their guidance and support throughout the development process.
