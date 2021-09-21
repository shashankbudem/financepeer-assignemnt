import MySQLdb.cursors
from flask import *
from flask_mysqldb import MySQL
import yaml
import os
from werkzeug.utils import secure_filename
import json
from jsonschema import validate

ALLOWED_EXTENSIONS = ['json']
UPLOAD_FOLDER = 'C:/Users/shashank/PycharmProjects/financepeer'

schema = {
    "type" : "object",
    "properties" : {
        "userId" : {"type":"number"},
        "id" : {"type":"number"},
        "title" : {"type":"string"},
        "body" : {"type":"string"},
    },
}

app = Flask(__name__)
app.secret_key = 'abc'
#configure database
db = yaml.load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['MYSQL_PORT'] = db['mysql_port']
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

mysql = MySQL(app)

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        userdetails = request.form
        username = userdetails['user']
        password = userdetails['pass']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(userid,password) VALUES(%s, %s)",(username,password))
        mysql.connection.commit()
        cur.close()
        return redirect('/login')
    return render_template('register.html')

@app.route('/logout')
def logout():
    if 'id' in session:
        session.pop('id',None)
    if 'username' in session:
        session.pop('username',None)
    if 'loggedin' in session:
        session.pop('loggedin',False)
    return redirect('/login')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        userdetails = request.form
        username = userdetails['user']
        password = userdetails['pass']
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        count = cur.execute("SELECT * FROM users WHERE userid = %s AND password = %s",(username,password))
        account = cur.fetchone()
        # mysql.connection.commit()
        # cur.close()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['userid']
            return redirect('/upload')
    return render_template('login.html')

@app.route('/upload')
def upload():
    if request.method == "POST":
        # if request.files:
        files = request.files["uploadfile"]
        print(files)
        return redirect("/success")
    return render_template('upload.html')


@app.route('/data', methods=['POST','GET'])
def data():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM files")
    dat = cur.fetchall()
    return render_template('data.html', dat=dat)

@app.route('/success', methods=['POST'])
def file_success():
    if request.method == 'POST':
        if 'uploadfile' not in request.files:
            # flash('No file uploaded')
            return 'No file uploaded'
        file = request.files['uploadfile']
        if file.filename == '':
            # flash('No file selected')
            return 'No file selected'
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'temp.json'))
            with open('temp.json') as f:
                data = json.load(f)
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM files")
            for x in data:
                # print(x['userId'], x['id'], x['title'], x['body'])
                cur.execute("INSERT INTO files(userid,id,title,body) VALUES(%s,%s,%s,%s)", (x['userId'], x['id'], x['title'], x['body']))
            mysql.connection.commit()
            cur.close()
            return redirect('/data')
    return "Failed" + file.filename

def allowed_file(filename):
    lst = filename.split(".")
    if lst[1] in ALLOWED_EXTENSIONS:
        # print(lst[1])
        return True
    return False

if __name__ == '__main__':
    app.run(debug=True)