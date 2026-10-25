from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
from pathlib import Path

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "inventory.db"

LOW_STOCK_THRESHOLD = 5


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_db_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                quantity INTEGER NOT NULL CHECK (quantity >= 0)
            )
        """)


HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Inventory System - v3</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f6f9;
            margin: 0;
            padding: 30px;
        }

        .container {
            max-width: 900px;
            margin: auto;
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
        }

        h1 {
            text-align: center;
            color: #243b55;
        }

        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 25px;
        }

        form {
            display: flex;
            gap: 10px;
            margin-bottom: 25px;
        }

        input {
            flex: 1;
            min-width: 0;
            padding: 12px;
            border: 1px solid #ccc;
            border-radius: 5px;
        }

        button {
            padding: 12px 18px;
            border: none;
            border-radius: 5px;
            background: #1769aa;
            color: white;
            cursor: pointer;
        }

        button:hover {
            background: #104d80;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }

        th, td {
            padding: 12px;
            border-bottom: 1px solid #ddd;
            text-align: left;
        }

        th {
            background: #eaf0f6;
        }

        .low-stock {
            color: #a11b1b;
            font-weight: bold;
        }

        .normal-stock {
            color: #176b2c;
            font-weight: bold;
        }

        .message {
            padding: 12px;
            margin-bottom: 15px;
            border-radius: 5px;
        }

        .success {
            background: #e3f7e8;
            color: #176b2c;
        }

        .error {
            background: #fde8e8;
            color: #a11b1b;
        }

        .alert {
            background: #fff0d5;
            color: #8a4b08;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }

        .empty {
            text-align: center;
            color: #777;
        }

        .summary {
            display: flex;
            gap: 15px;
            margin-bottom: 25px;
        }

        .card {
            flex: 1;
            padding: 18px;
            border-radius: 8px;
            background: #eaf0f6;
            text-align: center;
        }

        .card h3 {
            margin: 0 0 10px;
        }

        .card p {
            font-size: 25px;
            font-weight: bold;
            margin: 0;
        }

        @media (max-width: 600px) {
            body {
                padding: 10px;
            }

            form {
                flex-direction: column;
            }

            .summary {
                flex-direction: column;
            }

            th, td {
                padding: 7px;
                font-size: 13px;
            }
        }
    </style>
</head>

<body>
<div class="container">

    <h1>Inventory Management System</h1>

    <p class="subtitle">
        Version 3 — Low Stock Monitoring
    </p>

    {% if message %}
        <div class="message {{ message_type }}">
            {{ message }}
        </div>
    {% endif %}

    <div class="summary">
        <div class="card">
            <h3>Total Items</h3>
            <p>{{ total_items }}</p>
        </div>

        <div class="card">
            <h3>Low Stock Items</h3>
            <p>{{ low_stock_count }}</p>
        </div>
    </div>

    <h2>Add Inventory Item</h2>

    <form method="POST" action="{{ url_for('add_stock') }}">
        <input
            type="text"
            name="name"
            placeholder="Enter item name"
            maxlength="100"
            required
        >

        <input
            type="number"
            name="quantity"
            placeholder="Enter quantity"
            min="0"
            required
        >

        <button type="submit">Add Item</button>
    </form>

    <h2>All Inventory Items</h2>

    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Item Name</th>
                <th>Quantity</th>
                <th>Status</th>
            </tr>
        </thead>

        <tbody>
        {% for item in inventory %}
            <tr>
                <td>{{ item['id'] }}</td>
                <td>{{ item['name'] }}</td>
                <td>{{ item['quantity'] }}</td>
                <td>
                    {% if item['quantity'] <= threshold %}
                        <span class="low-stock">LOW STOCK</span>
                    {% else %}
                        <span class="normal-stock">In Stock</span>
                    {% endif %}
                </td>
            </tr>
        {% else %}
            <tr>
                <td colspan="4" class="empty">
                    No inventory items available.
                </td>
            </tr>
        {% endfor %}
        </tbody>
    </table>

    <h2>Low Stock Report</h2>

    <p>
        Items with {{ threshold }} units or fewer are classified as low stock.
    </p>

    {% if low_stock_items %}
        <div class="alert">
            <strong>Restocking Required</strong>

            <ul>
            {% for item in low_stock_items %}
                <li>
                    {{ item['name'] }} — {{ item['quantity'] }} units remaining
                </li>
            {% endfor %}
            </ul>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Item Name</th>
                    <th>Available Quantity</th>
                </tr>
            </thead>

            <tbody>
            {% for item in low_stock_items %}
                <tr>
                    <td>{{ item['name'] }}</td>
                    <td>{{ item['quantity'] }}</td>
                </tr>
            {% endfor %}
            </tbody>
        </table>
    {% else %}
        <div class="message success">
            No low-stock items found.
        </div>
    {% endif %}

</div>
</body>
</html>
"""


@app.route("/")
def home():
    initialize_database()

    with get_db_connection() as connection:
        inventory = connection.execute(
            "SELECT id, name, quantity FROM inventory ORDER BY id"
        ).fetchall()

    low_stock_items = [
        item for item in inventory
        if item["quantity"] <= LOW_STOCK_THRESHOLD
    ]

    message = request.args.get("message", "")
    message_type = request.args.get("type", "success")

    return render_template_string(
        HTML_PAGE,
        inventory=inventory,
        low_stock_items=low_stock_items,
        total_items=len(inventory),
        low_stock_count=len(low_stock_items),
        threshold=LOW_STOCK_THRESHOLD,
        message=message,
        message_type=message_type
    )


@app.route("/add", methods=["POST"])
def add_stock():
    initialize_database()

    name = request.form.get("name", "").strip()
    quantity_text = request.form.get("quantity", "").strip()

    if not name:
        return redirect(
            url_for(
                "home",
                message="Item name cannot be empty.",
                type="error"
            )
        )

    if len(name) > 100:
        return redirect(
            url_for(
                "home",
                message="Item name cannot exceed 100 characters.",
                type="error"
            )
        )

    try:
        quantity = int(quantity_text)

        if quantity < 0:
            raise ValueError

    except ValueError:
        return redirect(
            url_for(
                "home",
                message="Enter a valid non-negative quantity.",
                type="error"
            )
        )

    try:
        with get_db_connection() as connection:
            connection.execute(
                """
                INSERT INTO inventory (name, quantity)
                VALUES (?, ?)
                """,
                (name, quantity)
            )

    except sqlite3.IntegrityError:
        return redirect(
            url_for(
                "home",
                message="This item already exists. Use a different name.",
                type="error"
            )
        )

    return redirect(
        url_for(
            "home",
            message=f"Successfully added {name}.",
            type="success"
        )
    )


if __name__ == "__main__":
    initialize_database()

    app.run(
        host="127.0.0.1",
        port=5002,
        debug=True
    )