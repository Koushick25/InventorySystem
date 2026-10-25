from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
from pathlib import Path

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "inventory.db"

# Items with quantities at or below this value are considered low stock.
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

    <title>Inventory System - v2</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f6f9;
            margin: 0;
            padding: 30px;
        }

        .container {
            max-width: 1000px;
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
            padding: 12px;
            border: 1px solid #ccc;
            border-radius: 5px;
            min-width: 0;
        }

        .add-form input {
            flex: 1;
        }

        button {
            padding: 10px 15px;
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

        .low-stock {
            background-color: #fff0d5;
            color: #8a4b08;
            font-weight: bold;
        }

        .normal-stock {
            color: #176b2c;
            font-weight: bold;
        }

        .update-form {
            margin: 0;
            align-items: center;
        }

        .update-form input {
            width: 85px;
        }

        .empty {
            text-align: center;
            color: #777;
        }

        @media (max-width: 700px) {
            body {
                padding: 10px;
            }

            .add-form {
                flex-direction: column;
            }

            table {
                font-size: 13px;
            }

            th, td {
                padding: 7px;
            }

            .update-form {
                flex-direction: column;
            }
        }
    </style>
</head>

<body>
<div class="container">

    <h1>Inventory Management System</h1>

    <p class="version">
        Version 2 — Update Stock and Stock Alerts
    </p>

    {% if message %}
        <div class="message {{ message_type }}">
            {{ message }}
        </div>
    {% endif %}

    <h2>Add New Stock</h2>

    <form class="add-form" method="POST" action="{{ url_for('add_stock') }}">

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
            placeholder="Quantity"
            min="0"
            required
        >

        <button type="submit">Add Stock</button>

    </form>

    <h2>Current Inventory</h2>

    <p>
        Low-stock threshold: {{ threshold }} units or fewer.
    </p>

    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Item</th>
                <th>Current Quantity</th>
                <th>Stock Status</th>
                <th>Update Quantity</th>
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

                <td>
                    <form
                        class="update-form"
                        method="POST"
                        action="{{ url_for('update_stock', item_id=item['id']) }}"
                    >
                        <input
                            type="number"
                            name="quantity"
                            min="0"
                            value="{{ item['quantity'] }}"
                            required
                        >

                        <button type="submit">Update</button>
                    </form>
                </td>
            </tr>
        {% else %}
            <tr>
                <td colspan="5" class="empty">
                    No inventory items available.
                </td>
            </tr>
        {% endfor %}
        </tbody>
    </table>

    <h2>Low Stock Alerts</h2>

    {% if low_stock_items %}
        <div class="message error">
            <strong>Warning:</strong> The following items need restocking.
            <ul>
                {% for item in low_stock_items %}
                    <li>
                        {{ item['name'] }} — {{ item['quantity'] }} units remaining
                    </li>
                {% endfor %}
            </ul>
        </div>
    {% else %}
        <div class="message success">
            All inventory items have sufficient stock.
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
            message=f"Successfully added {name} to inventory.",
            type="success"
        )
    )


@app.route("/update/<int:item_id>", methods=["POST"])
def update_stock(item_id):
    initialize_database()

    quantity_text = request.form.get("quantity", "").strip()

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

    with get_db_connection() as connection:
        item = connection.execute(
            "SELECT id, name FROM inventory WHERE id = ?",
            (item_id,)
        ).fetchone()

        if item is None:
            return redirect(
                url_for(
                    "home",
                    message="Inventory item not found.",
                    type="error"
                )
            )

        connection.execute(
            "UPDATE inventory SET quantity = ? WHERE id = ?",
            (quantity, item_id)
        )

        item_name = item["name"]

    if quantity <= LOW_STOCK_THRESHOLD:
        message = (
            f"{item_name} updated successfully. "
            f"Low-stock alert: only {quantity} units remain."
        )
    else:
        message = f"{item_name} quantity updated successfully."

    return redirect(
        url_for(
            "home",
            message=message,
            type="success"
        )
    )


if __name__ == "__main__":
    initialize_database()

    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True
    )