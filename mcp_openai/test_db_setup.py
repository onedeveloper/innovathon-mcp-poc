import sqlite3

# Create a test database
conn = sqlite3.connect('test.db')
cursor = conn.cursor()

# Create test tables
cursor.execute('''
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    age INTEGER
)
''')

cursor.execute('''
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    product TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

# Insert test data
cursor.execute("INSERT INTO users (name, email, age) VALUES ('John Doe', 'john@example.com', 30)")
cursor.execute("INSERT INTO users (name, email, age) VALUES ('Jane Smith', 'jane@example.com', 25)")
cursor.execute("INSERT INTO users (name, email, age) VALUES ('Bob Johnson', 'bob@example.com', 40)")

cursor.execute("INSERT INTO orders (user_id, product, quantity, order_date) VALUES (1, 'Laptop', 1, '2025-04-01')")
cursor.execute("INSERT INTO orders (user_id, product, quantity, order_date) VALUES (1, 'Mouse', 2, '2025-04-02')")
cursor.execute("INSERT INTO orders (user_id, product, quantity, order_date) VALUES (2, 'Keyboard', 1, '2025-04-03')")

conn.commit()
conn.close()

print("Test database created successfully.")
