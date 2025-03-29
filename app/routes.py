# app/routes.py
from flask import Blueprint
from app.controllers.user_controller import home, add_user, get_users

main = Blueprint('main', __name__)

# Associate the controller functions with the routes
main.add_url_rule('/', 'home', home)
main.add_url_rule('/register', 'register', add_user, methods=['POST'])
main.add_url_rule('/get_users', 'get_users', get_users, methods=['GET'])
