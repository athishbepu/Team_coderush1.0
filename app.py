from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
import MySQLdb.cursors

app = Flask(__name__)
app.config.from_pyfile('config.py')

mysql = MySQL(app)
bcrypt = Bcrypt(app)

# ------------------ ROUTES ------------------
@app.route('/')
def home():
    return redirect(url_for('login'))

# ------------------ REGISTER ------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        age = request.form['age']
        gender = request.form['gender']
        location = request.form['location']

        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO users (name, email, phone, password, age, gender, location)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (name, email, phone, password, age, gender, location))
        mysql.connection.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

# ------------------ LOGIN ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        if user and bcrypt.check_password_hash(user['password'], password_input):
            session['loggedin'] = True
            session['id'] = user['id']
            session['name'] = user['name']
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password", "danger")
    return render_template('login.html')

# ------------------ DASHBOARD ------------------
@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        return render_template('chat.html', username=session['name'])
    return redirect(url_for('login'))

# ------------------ CHAT API ------------------
@app.route('/chat', methods=['POST'])
def chat():
    if 'loggedin' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_message = request.json.get('message')
    user_id = session['id']

    # Simple rule-based response for Phase 1
    if "fever" in user_message.lower():
        bot_reply = "It seems you might have a fever. Stay hydrated and rest. If symptoms persist, visit a doctor."
    elif "cough" in user_message.lower():
        bot_reply = "Cough detected. Drink warm fluids and monitor symptoms."
    else:
        bot_reply = "I am still learning. Can you describe your symptoms more clearly?"

    # Store chat log
    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO chat_logs (user_id, message, response)
        VALUES (%s, %s, %s)
    """, (user_id, user_message, bot_reply))
    mysql.connection.commit()

    return jsonify({"response": bot_reply})

if __name__ == '__main__':
    app.run(debug=True)
