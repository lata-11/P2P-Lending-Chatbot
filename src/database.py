from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi
uri = "mongodb+srv://shambhaviverma:197376200005@desis.a9ikza8.mongodb.net/?retryWrites=true&w=majority&appName=DESIS"

client = MongoClient(uri, server_api=ServerApi('1'))
db = client["P2PLend"]
try:
    client.admin.command('ping')
except Exception as e:
    print(e)


def group_creation(name, admin_id, admin_password, join_code, admin_name):
    
    record = {"name": name, "admin_id": admin_id, "admin_password": admin_password, "join_code": join_code}
    collection = db["Groups"]
    
    collection.insert_one(record)
    add_member(name, admin_id, admin_name)
    return True


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
    
def add_member(group_name,member_id,member_name):
    member_collections = db["Members"]
    group_id = db["Groups"].find_one({"name": group_name}).get("_id")
    existing_member = member_collections.find_one({"telegram_id": member_id})
    if existing_member:
        group_ids = existing_member.get("Group_id", [])
        if group_id not in group_ids:
            group_ids.append(group_id)
            member_collections.update_one({"telegram_id": member_id}, {"$set": {"Group_id": group_ids, "Member_name": member_name}})
            return True
        else:
            return False
    else:
        record = {"telegram_id": member_id, "Group_id": [group_id], "authentication details": 000, "points" : 0,"Member_name":member_name}
        member_collections.insert_one(record)
        return True

def get_admin_id(group_name):
    group = db["Groups"]
    document = group.find_one({"name": group_name})
    if document:
        return document.get("admin_id")
    return None

def is_join_code_correct(group_name, join_code):
    group = db["Groups"]
    document = group.find_one({"name": group_name, "join_code": join_code})
    return bool(document)

def is_group_exists(group_name):
    group = db["Groups"]
    document = group.find_one({"name": group_name})
    return bool(document)

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
