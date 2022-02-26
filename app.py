from flask import Flask, jsonify, request, url_for, redirect, session, render_template, g, flash
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import yaml
import datetime



# import pymysql
# import mysql.connector
#
# mydb = mysql.connector.connect(host='localhost', user='root', passwd='Hundo978!', auth_plugin='mysql_native_password', database="cs4400spring2020")
# mycursor = mydb.cursor(buffered=True)


import time
# from database import get_db, connect_db

app = Flask(__name__)

db_conf = yaml.safe_load(open('db.yaml'))
app.config['MYSQL_HOST'] = db_conf['mysql_host']
app.config['MYSQL_USER'] = db_conf['mysql_user']
app.config['MYSQL_PASSWORD'] = db_conf['mysql_password']
app.config['MYSQL_DB'] = db_conf['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  #So that results are not tuples....
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = '58fc483a-949a-487c-bfaa-da8a5923cd0e'

mysql = MySQL(app)
bootstrap =  Bootstrap(app)



@app.route('/')
def home():
    # session['username']='Clavel'
    # session.pop('username')
    return render_template("home.html")


@app.route('/csstest')
def csstest():
    return render_template("css.html")


@app.route('/dummy')
def dummy():
    return render_template("dummy.html")


@app.route('/admin')
def admin():
    return render_template("admin.html")


@app.route('/expenses')
def expenses():
    cur = mysql.connection.cursor()
    ret = cur.execute('''SELECT e.exp_id, e.descr, e.amount, e.month, e.day, e.year,  v.vendor, c.cat 
    FROM expenses e  JOIN vendors v ON (e.vendor_id = v.vendor_id) 
    JOIN cats c on (e.cat_id = c.cat_id) ORDER BY e.month, e.day ''')

    if ret:
        expenses = cur.fetchall()
        return render_template("expenses.html", expenses=expenses)


@app.route('/exp_mo/<int:mo>')
def exp_mo(mo):
    cur = mysql.connection.cursor()
    ret = cur.execute('''SELECT e.exp_id, e.descr, e.amount, e.month, e.day, e.year,  v.vendor, c.cat 
    FROM expenses e  JOIN vendors v ON (e.vendor_id = v.vendor_id) 
    JOIN cats c on (e.cat_id = c.cat_id) WHERE e.month = {} ORDER BY e.month, e.day'''.format(mo))
    if ret:
        expenses = cur.fetchall()

        s= cur.execute('''SELECT c.cat, SUM(e.amount) as sum FROM expenses e JOIN cats c on(e.cat_id = c.cat_id) WHERE e.month = {} GROUP BY c.cat ORDER BY c.cat'''.format(mo))
        if s:
            sums = cur.fetchall()
        return render_template("expenses.html", expenses=expenses, sums=sums)




@app.route('/macro_exp')
def macro_exp():
    cur = mysql.connection.cursor()
    ret = cur.execute(
        '''SELECT exp_id, descr, amount, exp_date, cat_id, vendor_id FROM expenses ORDER BY exp_date DESC''')
    if ret:
        exp_dict = {}
        expenses = cur.fetchall()
        return render_template("macro_exp.html", expenses=expenses)


@app.route('/cats')
def categories():
    cur = mysql.connection.cursor()
    ret = cur.execute('''SELECT cat_id, cat, status FROM cats ORDER BY cat''')
    if ret:
        cats = cur.fetchall()
        return render_template("categories.html", cats=cats)
    cur.close()

@app.route('/vendors')
def vendors():
    cur = mysql.connection.cursor()
    ret = cur.execute('''SELECT vendor_id, vendor, status FROM vendors ORDER BY vendor''')
    if ret:
        vendors = cur.fetchall()
        return render_template("vendors.html", vendors=vendors)
    cur.close()

@app.route('/xyz')
def xyz():
    if 'username' in session:
        return format("<h3>{}</h3>").format(session['username'])
    else:
        return "No username in session"


@app.route('/addexp', methods=['GET', 'POST'])
def addexp():
    if request.method == 'POST':
        form = request.form
        descr = form['descr']
        amount = form['amount']
        exp_date = form['exp_date']
        cat_id = form['cat_id']
        vendor_id = form['vendor_id']

        cur = mysql.connection.cursor()
        cur.execute(''' INSERT INTO expenses(descr, amount, exp_date, cat_id, vendor_id) 
    VALUES (%s,%s,%s,%s,%s)''', (descr, amount, exp_date, cat_id, vendor_id))
        mysql.connection.commit()
        cur.close()
        flash("Expense recorded: {}".format(descr))
        return render_template('dummy.html')

    d = datetime.datetime.now()
    d_int= d.strftime("%d")
    m_int = d.strftime("%m")
    return render_template('addexp.html', month=m_int, day=d_int)


@app.route('/logout')
def logout():
    if 'username' in session:
        un = session['username']
        session['login'] = 'False'
        session.pop('username')
        session.pop('user_id')
        session.pop('firstname')
        session.pop('lastname')
        flash("{} logged out".format(un))
        return redirect('/')
    else:
        return "There was no active user to be logged out"


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data_in = request.form
        if data_in['password'] != data_in['confirm_password']:
            flash('Passwords do not match. Try again.', 'danger')
            return render_template('register.html')
        firstname = data_in['firstname']
        lastname = data_in['lastname']
        username = data_in['username']
        email = data_in['email']

        pw = data_in['password']
        pwhash = generate_password_hash(pw)
        cur = mysql.connection.cursor()
        cur.execute(''' INSERT INTO users(firstname, lastname, username, email, password) VALUES (%s,%s,%s,%s,%s)''',
                    (firstname, lastname, username, email, pwhash))
        mysql.connection.commit()
        cur.close()
        flash('Registration successful. Please log in.', 'success')
        # session['username'] = username
        return redirect('/login')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data_in = request.form
        username = data_in['username']
        pw_in = data_in['password']

        cur = mysql.connection.cursor()
        ret = cur.execute("SELECT user_id, firstname, lastname, username,  password FROM users WHERE username = '{}'".format(username))
        if ret:
            user = cur.fetchone()

            if check_password_hash(user['password'], pw_in):
                session['login'] = 'True'
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['firstname'] = user['firstname']
                session['lastname'] = user['lastname']
                flash('Welcome, ' + session['firstname'] + '! You have successfully logged in.',  'success')
                return redirect('/')
            else:
    #             print('168')
    #             cur.close()
                flash('Password does not match', 'danger')
                # return render_template('dummy2.html')
                return render_template('login.html')
            # print('172')
    #         # return render_template('dummy.html')
    #         return 'app.py 175'
    #
    #     else:
    #         print('175')
    #         cur.close()
    #         # flash('User not found', 'danger')
    #         return render_template('login.html')
    #         # return "Vete, carajo!"
    #     print('188')
        cur.close()
    #     return redirect('/')
    # print('183')
    return render_template('login.html')


@app.route('/write' , methods = ['GET', 'POST'])
def write():
# Write a new blog
# CREATE TABLE blogs (blog_id INT PRIMARY KEY AUTO_INCREMENT, title  VARCHAR(50), author_id INT, text TEXT);
    if request.method == 'POST':
        post = request.form
        title = post['title']
        text = post['text']
        author_id = session['user_id']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO blogs(title, text, author_id) VALUES(%s, %s, %s)", (title, text, author_id))
        mysql.connection.commit()
        cur.close()
        flash("Successfully posted new blog", 'success')
        return redirect('/posts')
    return render_template('write.html')



@app.route('/editpost/<int:id>' , methods = ['GET', 'POST'])
def editpost():
    return render_template("editpost.html")


@app.route('/deletepost/<int:id>/' , methods = ['POST'])
def deletepost(id):
    return 'Post deleted'


@app.route('/posts')
def posts():
    author_id = session['user_id']
    cur = mysql.connection.cursor()
    result_value = cur.execute("SELECT * FROM blogs WHERE author_id = %s", [author_id])
    if result_value > 0:
        hisher_blogs = cur.fetchall()
        cur.close()
        return render_template('posts.html', blogs=hisher_blogs)
    cur.close()
    return render_template('posts.html', blogs=None)

@app.route('/posts_all')
def posts_all():
    author_id = session['user_id']
    cur = mysql.connection.cursor()
    result_value = cur.execute("SELECT * FROM blogs ")
    if result_value > 0:
        hisher_blogs = cur.fetchall()
        cur.close()
        return render_template('posts.html', blogs=hisher_blogs)
    cur.close()
    return render_template('posts.html', blogs=None)



@app.route('/post/<int:id>/')
def post(id):
    print('249: ', id)
    cur = mysql.connection.cursor()
    result_value = cur.execute("SELECT * FROM blogs WHERE blog_id = %s", (id,))
    print('251: ', result_value)
    if result_value == 1:
        the_blog = cur.fetchone()
        print('253: ', the_blog)
        cur.close()
        return render_template('post.html', blog=the_blog)
    return "The blog post was not found."
    return render_template("post.html", id=id)



@app.route('/authors')
def authors():
    return render_template("authors.html", title_searching=True)

@app.route('/title_search', methods=['GET','POST'])
def title_search():
    param = request.form['title_search'].upper()
    cur = mysql.connection.cursor()
    q = """SELECT t.title_id, t.title, concat(a.firstname, ' ', a.lastname) AS authname, t.pub_year, t.price, t.img_url FROM titles t JOIN authors a 
    ON t.author_id = a.author_id JOIN keywords kw on t.title_id = kw.title_id WHERE kw.kw LIKE '%{}%' """.format(param)
    ret = cur.execute(q)
    if ret:
        results = cur.fetchall()
        return render_template('title_search.html', results = results)

    # return request.form['title_search']
    # return render_template("authors.html")



@app.route('/translators')
def translators():
    return render_template("translators.html")

@app.route('/titles')
def titles():
    cur = mysql.connection.cursor()
    ret = cur.execute('''SELECT t.title_id, t.title, t.pub_year, t.price, t.img_url, concat(a.firstname, ' ', a.lastname) authname
     FROM titles t JOIN authors a on t.author_id=a.author_id ORDER BY t.title''')
    if ret:
        titles = cur.fetchall()
        return render_template("titles.html", titles=titles)
    cur.close()


if __name__ == '__main__':
    app.run(debug=True)