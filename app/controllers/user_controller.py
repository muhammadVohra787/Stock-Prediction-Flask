# app/controllers/user_controller.py
from flask import jsonify, request, render_template
from app import mongo
def home():
    return render_template("register.html")

def add_user():
    # Get form data from the request
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    password = request.form.get('password')
    amount = request.form.get('amount')  # The selected trading amount

    # Optionally: Validate the form data (e.g., check if required fields are empty)
    if not full_name or not email or not password or not amount:
        return jsonify({"message": "All fields are required!"}), 400

    # Insert data into MongoDB
    user_data = {
        "full_name": full_name,
        "email": email,
        "password": password,  # You may want to hash the password before storing it
        "amount": amount
    }
    
    mongo.db.users.insert_one(user_data)  # Insert data into 'users' collection

    return jsonify({"message": "User registered successfully!"}), 201

def get_users():
    users = list(mongo.db.users.find({}))  # Get all users, exclude _id
    for user in users:
        user['_id'] = str(user['_id'])  # Convert ObjectId to string
    return jsonify(users)
    
