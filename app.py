from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL

app = Flask(__name__)
app.config.from_pyfile('config.py')

mysql = MySQL(app)

# ------------------ ROUTES ------------------
@app.route('/')
def home():
    return redirect(url_for('login'))

# ------------------ REGISTER ------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')
        age = data.get('age')
        gender = data.get('gender')
        location = data.get('location')
        if not password:
            return {"success": False, "message": "Password cannot be empty."}
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO users (name, email, phone, password, age, gender, location)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, email, phone, password, age, gender, location))
        mysql.connection.commit()
        return {"success": True, "message": "Registration successful!"}
    return render_template('register.html')

# ------------------ LOGIN ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT * FROM users WHERE email=%s OR phone=%s
        """, (username, username))
        user = cursor.fetchone()
        print("User:", user)
        if not user:
            return {"success": False, "message": "Invalid credentials."}
        print("Password from DB:", user[4])
        print("Password from form:", password)
        if user[4] == password:
            session['loggedin'] = True
            session['id'] = user[0]
            session['name'] = user[1]
            return {"success": True, "message": "Login successful!"}
        else:
            return {"success": False, "message": "Invalid credentials."}
    return render_template('login.html')

# ------------------ DASHBOARD ------------------
@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        return render_template('dashboard.html', username=session['name'])
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
