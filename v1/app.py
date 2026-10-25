from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
from pathlib import Path

app = Flask(__name__)

# Store the database inside the v1 directory.
BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "inventory.db"


def get_db_connection():
    """Create a connection to the SQLite database."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """Create the inventory table if it does not exist."""
    with get_db_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                quantity INTEGER NOT NULL CHECK (quantity >= 0)
            )
        """)


# HTML page for the v1 application.
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Inventory System - v1</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f6f9;
            margin: 0;
            padding: 30px;
        }

        .container {
            max-width: 850px;
            margin: auto;
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
        }

        h1 {
            color: #243b55;
            text-align: center;
        }

        .version {
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
            padding: 12px;
            border: 1px solid #ccc;
            border-radius: 5px;
        }

        button {
            padding: 12px 18px;
            background-color: #1769aa;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }

        button:hover {
            background-color: #104d80;
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
            background-color: #eaf0f6;
        }

        .message {
            padding: 12px;
            margin-bottom: 15px;
            border-radius: 5px;
        }

        .success {
            background-color: #e3f7e8;
            color: #176b2c;
        }

        .error {
            background-color: #fde8e8;
            color: #a11b1b;
        }

        .empty {
            text-align: center;
            color: #777;
        }

        @media (max-width: 600px) {
            body {
                padding: 10px;
            }

            form {
                flex-direction: column;
            }
        }
    </style>
</head>

<body>
    <div class="container">

        <h1>Inventory Management System</h1>

        <p class="version">
            Version 1 — Add Stock
        </p>

        {% if message %}
            <div class="message {{ message_type }}">
                {{ message }}
            </div>
        {% endif %}

        <h2>Insert New Stock</h2>

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

            <button type="submit">Add Stock</button>

        </form>

        <h2>Current Inventory</h2>

        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Item Name</th>
                    <th>Quantity</th>
                </tr>
            </thead>

            <tbody>
                {% for item in inventory %}
                    <tr>
                        <td>{{ item['id'] }}</td>
                        <td>{{ item['name'] }}</td>
                        <td>{{ item['quantity'] }}</td>
                    </tr>
                {% else %}
                    <tr>
                        <td colspan="3" class="empty">
                            No inventory items available.
                        </td>
                    </tr>
                {% endfor %}
            </tbody>
        </table>

    </div>
</body>
</html>
"""


@app.route("/")
def home():
    """Display the inventory page."""
    initialize_database()

    with get_db_connection() as connection:
        inventory = connection.execute(
            "SELECT id, name, quantity FROM inventory ORDER BY id"
        ).fetchall()

    message = request.args.get("message", "")
    message_type = request.args.get("type", "success")

    return render_template_string(
        HTML_PAGE,
        inventory=inventory,
        message=message,
        message_type=message_type
    )


@app.route("/add", methods=["POST"])
def add_stock():
    """Insert a new inventory item."""
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
            message=f"Successfully added {name} to inventory.",
            type="success"
        )
    )


if __name__ == "__main__":
    initialize_database()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )