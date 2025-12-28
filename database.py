"""
Database module for storing orders in SQLite for Metabase analytics
"""
import sqlite3
import json
from datetime import datetime
import os

DB_FILE = 'delicatessen.db'

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT UNIQUE NOT NULL,
            customer TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL,
            notes TEXT,
            driver TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create order_items table (normalized for better analytics)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes for better query performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_timestamp ON orders(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_order_items_item_name ON order_items(item_name)')
    
    conn.commit()
    conn.close()

def save_order_to_db(order_data):
    """
    Save an order to the database
    order_data should have: code, customer, timestamp, total, status, notes, items (dict), driver (optional)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Insert order - use order_id from order_data if available, otherwise use order_code
        order_code = order_data.get('code') or f"P{order_data.get('id', 0):03d}"
        
        cursor.execute('''
            INSERT INTO orders (order_code, customer, timestamp, total, status, notes, driver)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_code,
            order_data.get('customer', 'Cliente Ocasional'),
            order_data.get('timestamp'),
            order_data.get('total', 0),
            order_data.get('status', 'pending'),
            order_data.get('notes', ''),
            order_data.get('driver')
        ))
        
        order_id = cursor.lastrowid
        
        # Insert order items
        items = order_data.get('items', {})
        for item_name, item_details in items.items():
            if isinstance(item_details, dict):
                quantity = item_details.get('quantity', 0)
                price = item_details.get('price', 0)
            else:
                # Fallback for old format
                quantity = int(item_details) if isinstance(item_details, (int, str)) else 0
                price = 0  # Will need to look up from menu
            
            cursor.execute('''
                INSERT INTO order_items (order_id, item_name, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item_name, quantity, price))
        
        conn.commit()
        return order_id
    except sqlite3.IntegrityError as e:
        # Order code already exists, try to update instead
        conn.rollback()
        cursor.execute('SELECT id FROM orders WHERE order_code = ?', (order_data.get('code'),))
        existing = cursor.fetchone()
        if existing:
            order_id = existing['id']
            # Update order
            cursor.execute('''
                UPDATE orders 
                SET customer = ?, timestamp = ?, total = ?, status = ?, notes = ?, driver = ?
                WHERE id = ?
            ''', (
                order_data.get('customer', 'Cliente Ocasional'),
                order_data.get('timestamp'),
                order_data.get('total', 0),
                order_data.get('status', 'pending'),
                order_data.get('notes', ''),
                order_data.get('driver'),
                order_id
            ))
            # Delete old items and insert new ones
            cursor.execute('DELETE FROM order_items WHERE order_id = ?', (order_id,))
            items = order_data.get('items', {})
            for item_name, item_details in items.items():
                if isinstance(item_details, dict):
                    quantity = item_details.get('quantity', 0)
                    price = item_details.get('price', 0)
                else:
                    quantity = int(item_details) if isinstance(item_details, (int, str)) else 0
                    price = 0
                cursor.execute('''
                    INSERT INTO order_items (order_id, item_name, quantity, price)
                    VALUES (?, ?, ?, ?)
                ''', (order_id, item_name, quantity, price))
            conn.commit()
            return order_id
        else:
            raise
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()

def update_order_status(order_id, status):
    """Update order status in database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
    conn.commit()
    conn.close()

def assign_driver_to_order(order_id, driver):
    """Assign a driver to an order"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET driver = ? WHERE id = ?', (driver, order_id))
    conn.commit()
    conn.close()

def unassign_driver_from_order(order_id):
    """Remove driver assignment from an order"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET driver = NULL WHERE id = ?', (order_id,))
    conn.commit()
    conn.close()

# Initialize database on import
if not os.path.exists(DB_FILE):
    init_database()

