from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi
uri = "mongodb+srv://shambhaviverma:197376200005@desis.a9ikza8.mongodb.net/?retryWrites=true&w=majority&appName=DESIS"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["P2PLend"]
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

def add_member(group_name, join_code,member_name, telegram_id, authentication_details, permission, password):
    if not(permission):
        return "Permission to join the group denied"
    group = db["Groups"]
    document = group.find_one({"name": group_name})
    if not (document):
        return "No such group exists"
       
    if not (group.find_one({"name": group_name, "join_code": join_code})):
        return "Group Join Code Incorrect"
    
    group_id = document.get("_id")
    if not authenticate(authentication_details):
         return "Member details are not authentic"
    
    record = {"Member_name": member_name, "Group_id": group_id, "telegram_id": telegram_id,"password":password, "authentication details": authentication_details, "points" : 0}
    member_collections = db["Members"]
    if (member_collections.find_one({"telegram_id": telegram_id})):
        return "Member already present in group"
    member_collections.insert_one(record)
    return "Successfully added in group"

def add_transaction(borrower_id, lender_id, group_id, amount, time):
    transaction = db["Transaction"]
    record = {"Borrower_id": borrower_id, "Lender_id": lender_id, "Group_id": group_id, "Amount": amount, "Time" : time, "Return_status": "Pending"}
    transaction.insert_one(record)

def admin_login(admin_id, admin_password, group_name):
    group = db["Groups"]
    if not (group.find_one({"admin_id": admin_id, "admin_password": admin_password, "name": group_name})):
        return "Incorrect Credentials"
    
def remove_member(member_name, group_name):
    collection = db["Members"]
    group_id = db["Groups"].find_one({"name": group_name}).get("_id")
    print(group_id)
    result = collection.delete_one({"Member_name": member_name, "Group_id": group_id})
    if result.deleted_count == 1:
        return "Member removed successfully."
    else:
        return "Entry not found." 

def lend_proposals(lender_tid, group_name, interest, borrower_tid):#tid is the telegram id
    collection = db["Active_Proposals"]
    group_id = db["Groups"].find_one({"name": group_name}).get("_id")
    record = {"group_id": group_id, "lender_id": lender_tid, "borrower_id": borrower_tid, "interest": interest}
    collection.insert_one(record)
    return "Offer made successfully"


def display_proposals(member_id,group_name):
    collection = db["Active_Proposals"]
    group_id = db["Groups"].find_one({"name": group_name}).get("_id")
    proposals = collection.find({"borrower_id": member_id, "group_id": group_id}, {"_id": 1, "interest": 1})
    return proposals
