# Goal of the script : manage food inventory, perishables, recipes, shopping list...
# Author : Nitrox
import os

import pymysql
from pymysql.cursors import DictCursor

from datetime import datetime, timedelta
from typing import Optional

from nicegui import ui, app

def header():
    ui.add_head_html("""
        <style>
        body.body--dark {
            background-color: #080e1a  !important;
        }
        .q-page {
            background-color: #080e1a  !important;
        }
        </style>
        """)
    with ui.header(fixed=False).style('background-color: #395c7f').classes('w-full'):
        ui.button('Home', on_click=lambda: ui.navigate.to('/')).props('flat color=white bold')
        ui.button('Inventory', on_click=lambda: ui.navigate.to('/inventory')).props('flat color=white bold')
        ui.button('Shopping List', on_click=lambda: ui.navigate.to('/shopping-list')).props('flat color=white bold')

# Database Functions

def get_connection():
    return pymysql.connect(
        host='db',
        user='root',
        password=os.getenv('MYSQL_ROOT_PASSWORD', 'example_password'),
        database='food_db'
    )

def create_tables():
    connection = get_connection()
    cursor = connection.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_items (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            quantity INT NOT NULL,
            expiration_date DATE,
            added_date DATE NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255) NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shopping_list (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            item_name VARCHAR(255) NOT NULL,
            quantity INT NOT NULL,
            added_date DATE NOT NULL,
            marked BOOLEAN DEFAULT FALSE
        )
    ''')

    connection.commit()
    cursor.close()
    connection.close()

def add_food_item(name, quantity, expiration_date: Optional[datetime] = None):
    con = get_connection()
    with con.cursor(DictCursor) as cursor:
        cursor.execute('''
            INSERT INTO food_items (name, quantity, expiration_date, added_date)
            VALUES (%s, %s, %s, %s)
        ''', (name, quantity, expiration_date, datetime.now()))
        con.commit()
    con.close()

# Pages

@ui.page('/')
def home_page():
    header()
    ui.markdown('## Welcome to FoodManager!')
    ui.markdown('Use the navigation buttons above to manage your inventory and shopping list.')
    
@ui.page('/inventory')
def inventory_page():
    def add_item(name, quantity, expiration_date):
        if not name or quantity <= 0:
            ui.notify('Please enter a valid name and quantity.', color='red')
            return
        add_food_item(name, quantity, expiration_date if expiration_date else None)
        ui.notify(f'Added {quantity} x {name} to inventory.', color='green')
        items = get_inventory_items()
        show_inventory(items, container)
    
    
    def get_inventory_items():
        con = get_connection()
        with con.cursor(DictCursor) as cursor:
            cursor.execute('SELECT * FROM food_items ORDER BY expiration_date ASC')
            items = cursor.fetchall()
        con.close()
        return items
    
    def show_inventory(items, container):
        container.clear()
        with container:
            if not items:
                ui.markdown('No items in inventory. Add some food items!')
                return
            with ui.table(columns=[{'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True}, 
                                        {'name': 'quantity', 'label': 'Quantity', 'field': 'quantity', 'sortable': True}, 
                                        {'name': 'expiration_date', 'label': 'Expiration Date', 'field': 'expiration_date', 'sortable': True}, 
                                        {'name': 'added_date', 'label': 'Added Date', 'field': 'added_date', 'sortable': True}], rows=[], row_key='id').classes('w-full') as table:
                for item in items:
                    table.add_row(item)
    header()
    ui.markdown('## Inventory')
    items = get_inventory_items()
    container = ui.column()
    show_inventory(items, container)

@ui.page('/shopping-list')
def shopping_list_page():
    header()
    ui.markdown('## Shopping List')

create_tables()

ui.run(title='FoodManager', port=5000, reload=True, dark=True, favicon='🍔')