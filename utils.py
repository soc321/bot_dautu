import json, os
from datetime import datetime
from config import MIN_WITHDRAW, MAX_WITHDRAW

DATA_FILE = "users.json"

def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_or_create_user(user_id, data=None):
    if data is None:
        data = load_users()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "balance": 0,
            "investments": [],
            "withdrawals": [],
            "deposits": [],
            "bank": "-",
            "bank_number": "-",
        }
        save_users(data)
    return data[uid]

def invest(user_id, package):
    data = load_users()
    user = get_or_create_user(user_id, data)
    user["investments"].append({
        "amount": package["amount"],
        "daily": package["daily"],
        "days": package["days"],
        "start": current_time()
    })
    save_users(data)

def calculate_profit(user_id):
    from datetime import datetime
    user = get_or_create_user(user_id)
    now = datetime.now()
    total = 0
    for inv in user["investments"]:
        start = datetime.strptime(inv["start"], "%Y-%m-%d %H:%M:%S")
        elapsed = (now - start).days
        total += min(elapsed, inv["days"]) * inv["daily"]
    return total

def withdraw(user_id, amount):
    data = load_users()
    user = get_or_create_user(user_id, data)
    profit = calculate_profit(user_id)
    withdrawn = sum(w["amount"] for w in user["withdrawals"])
    available = profit - withdrawn
    if MIN_WITHDRAW <= amount <= MAX_WITHDRAW and amount <= available:
        user["withdrawals"].append({"amount": amount, "time": current_time()})
        save_users(data)
        return True
    return False
