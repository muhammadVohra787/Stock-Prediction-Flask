# app/routes.py
from flask import Blueprint
from app.controllers.user_controller import home, add_user, get_users, stock_selected, buy_stock, sell_stock, get_holdings, login_user, logout_user, home_page, get_balance

main = Blueprint('main', __name__)

# Associate the controller functions with the routes
# main.add_url_rule('/', 'home', home)
# New default home route (public landing page)
main.add_url_rule('/', 'home_page', home_page)
main.add_url_rule('/dashboard', 'home', home)  
main.add_url_rule('/register', 'register', add_user, methods=['GET', 'POST'])
main.add_url_rule('/get_users', 'get_users', get_users, methods=['GET'])
main.add_url_rule('/stock_selected', 'stock_selected' ,stock_selected,methods=['POST'])
main.add_url_rule('/buy_stock', 'buy_stock', buy_stock, methods=['POST'])
main.add_url_rule('/sell_stock', 'sell_stock', sell_stock, methods=['POST'])
main.add_url_rule('/user_holdings/<user_id>', 'user_holdings', get_holdings, methods=['GET'])
main.add_url_rule('/login', 'login', login_user, methods=['GET', 'POST'])
main.add_url_rule('/logout', 'logout', logout_user)
main.add_url_rule('/balance', 'get_balance', get_balance, methods=['GET'])
