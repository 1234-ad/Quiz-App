
from flask import Flask, render_template, request, redirect, session, url_for
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd

app = Flask(__name__)
app.secret_key = 'supersecretkey'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'your_mysql_password'
app.config['MYSQL_DB'] = 'quiz_app'

mysql = MySQL(app)

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('quiz'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, password FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            return redirect(url_for('quiz'))
    return render_template('login.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        df = pd.read_excel(file)
        cur = mysql.connection.cursor()
        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct_ans)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (row['Question'], row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D'], row['Correct_Ans']))
        mysql.connection.commit()
        cur.close()
        return 'Questions uploaded successfully'
    return render_template('upload.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM questions")
    questions = cur.fetchall()
    cur.close()
    return render_template('quiz.html', questions=questions)

@app.route('/submit', methods=['POST'])
def submit():
    user_id = session['user_id']
    answers = request.form.to_dict()
    cur = mysql.connection.cursor()
    score = 0
    for qid, ans in answers.items():
        cur.execute("SELECT correct_ans FROM questions WHERE id=%s", (qid,))
        correct = cur.fetchone()[0]
        is_correct = (ans == correct)
        if is_correct:
            score += 1
        cur.execute("""
            INSERT INTO user_answers (user_id, question_id, selected_ans, is_correct)
            VALUES (%s, %s, %s, %s)
        """, (user_id, qid, ans, is_correct))
    mysql.connection.commit()
    cur.close()
    return render_template('result.html', score=score, total=len(answers))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
