from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt

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
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        age = request.form.get('age')
        gender = request.form.get('gender')
        location = request.form.get('location')
        if not password:
            flash('Password cannot be empty.', 'danger')
            return render_template('register.html')
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO users (name, email, phone, password, age, gender, location)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, email, phone, hashed_pw, age, gender, location))
        mysql.connection.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# ------------------ LOGIN ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT * FROM users WHERE email=%s OR phone=%s
        """, (username, username))
        user = cursor.fetchone()
        if user and bcrypt.check_password_hash(user[4], password):
            session['loggedin'] = True
            session['id'] = user[0]
            session['name'] = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')

# ------------------ DASHBOARD ------------------
@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        return render_template('dashboard.html', username=session['name'])
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
