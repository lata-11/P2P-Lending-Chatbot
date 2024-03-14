from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi
uri = "mongodb+srv://shambhaviverma:197376200005@desis.a9ikza8.mongodb.net/?retryWrites=true&w=majority&appName=DESIS"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'), tlsCAFile=certifi.where())
db = client["P2PLend"]
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
except Exception as e:
    print(e)

def authenticate():
     #check if the details are authentic or not
     return True

def group_creation(name, admin_id, admin_password, join_code):
    
    record = {"name": name, "admin_id": admin_id, "admin_password": admin_password, "join_code": join_code}
    collection = db["Groups"]

    if(collection.find_one({"name":name})):
        return "Group Name Not Available"
    
    collection.insert_one(record)
    return "Group Created"

def add_member(group_name, join_code, member_id, authentication_details):

    group = db["Groups"]
    document = group.find_one({"name": group_name})
    if not (document):
        return "No such group exists"
       
    if not (group.find_one({"name": group_name, "join_code": join_code})):
        return "Group Join Code Incorrect"
    
    group_id = document.get("Group_id")
    if not authenticate():
         return "Member details are not authentic"
    
    record = {"Member_name": member_id, "Group_id": group_id, "authentication details": authentication_details, "points" : 0}
    member_collections = db["Members"]
    member_collections.insert_one(record)

def add_transaction(borrower_id, lender_id, group_id, amount, time):
    transaction = db["Transaction"]
    record = {"Borrower_id": borrower_id, "Lender_id": lender_id, "Group_id": group_id, "Amount": amount, "Time" : time, "Return_status": "Pending"}
    transaction.insert_one(record)

def admin_login(admin_name, admin_password, group_id):
    #powers of admin
     group = db["Groups"]
     if not (group.find_one({"admin_name": admin_name, "admin_password": admin_password, "group_id": group_id})):
         return "Incorrect Credentials"
     #powers of admin

    
