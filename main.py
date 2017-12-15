from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from hashlib import sha256
import random as rnd
import string

# ~~~~~~~~~~~~~~~

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = ('mysql+pymysql://nodal_test:nodal_test@localhost:8889/nodal_test')
app.config['SECRET_KEY'] = 'a9sdbf53a85143iblhfg69omfeh465g4bk3hq2emp1nk'
db = SQLAlchemy(app)

# ~~~~~~ db.Model Classes ~~~~~~

class User(db.Model):
	
	ID = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(12), unique=True, nullable=False)
	password = db.Column(db.String(100), nullable=False)
	salt = db.Column(db.String(4), nullable=False)

	def __init__(self, name, password, salt):
		self.username = name
		self.password = password
		self.salt = salt

	def __str__(self):
		return ('<USER: {id}::{name}>'.format(id=self.ID, name=self.username))

class Node(db.Model):
	
	ID = db.Column(db.Integer, primary_key=True)
	UID = db.Column(db.Integer, db.ForeignKey('user.ID'), nullable=False)
	name = db.Column(db.String(100), unique=True, nullable=False)
	content = db.Column(db.Text)
	timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

	def __init__(self, userId, name, content):
		self.UID = userId
		self.name = name
		self.content = content

	def addLink(self, user, id):
		link = Link(user, self.ID, id)
		db.session.add(link)
		db.session.commit()

	def __str__(self):
		return ('<NODE: {id}::{name}>'.format(id=self.ID, name=self.name))

class Link(db.Model):
	
	ID = db.Column(db.Integer, primary_key=True)
	UID = db.Column(db.Integer, db.ForeignKey('user.ID'), nullable=False)
	node1 = db.Column(db.Integer, db.ForeignKey('node.ID'), nullable=False)
	node2 = db.Column(db.Integer, db.ForeignKey('node.ID'), nullable=False)
	content = db.Column(db.String(100))
	timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

	def __init__(self, userId, n1, n2):
		self.UID = userId
		self.node1 = n1
		self.node2 = n2

	def __str__(self):
		return ('<LINK: {id}::[{n1}, {n2}]>'.format(id=self.ID, n1=self.node1, n2=self.node2))

# ~~~~~~~~~~~~~~~

def validate_username(name):
	if (2 < len(name) < 13):
		return True
	else:
		return False

def validate_password(pwd):
	if (3 < len(pwd) < 13):
		return True
	else:
		return False

def hash_password(pwd, salt):
	return sha256(str.encode(pwd + salt)).hexdigest()

def generate_salt(len):
	return ''.join([rnd.choice(string.ascii_letters) for i in range(4)])

def get_user():
	return (User.query.filter_by(ID=session['user']).first() if ('user' in session) else None)


# ~~~~~~~~~~~~~~~

@app.route("/")
def index():
	return render_template('index.html', title='flask testing')

@app.route("/resume")
def resume():
	return render_template('resume.html', title='resume')

@app.route("/random")
def random():
	return render_template('random.html', title='something')

@app.route("/robot.txt")
def robot():
	return("beep boop")

# ~~~~ nodal ~~~~

@app.before_request
def session_check():
	allowed_routes = ['index', 'resume', 'random', 'static', 'robot', 'nodalLogin', 'nodalSignup']
	if (request.endpoint not in allowed_routes):
		if ('user' not in session):
			flash("oops - looks like you're not logged in")
			return redirect('nodal/login')
		else:
			user = User.query.filter_by(ID=session['user']).first()
			if (user is None):
				flash("uhhhhh")
				del session['user']
				return redirect('nodal/login')

@app.route("/nodal")
def nodalHome():
	user = get_user().username
	return render_template('nodal.html', title='nodal :: ' + user, user=user)

@app.route("/nodal/login", methods=['GET', 'POST'])
def nodalLogin():

	if (request.method == 'POST'):
		name = request.form['username']
		pwd = request.form['password']

		user = User.query.filter_by(username=name).first()

		if (not user):
			# no such user
			return render_template('nodal_login.html', title='nodal :: login', name_err='no such user')

		pwd_check = hash_password(pwd, user.salt)

		if (user.password != pwd_check):
			# incorrect password
			return render_template('nodal_login.html', title='nodal :: login', pwd_err='wrong password',
				username=name)

		session['user'] = user.ID

		return redirect('/nodal')

	return render_template('nodal_login.html', title='nodal :: login')

@app.route('/nodal/signup', methods=['GET', 'POST'])
def nodalSignup():

	if (request.method == 'POST'):

		name = request.form['username']
		pwd1 = request.form['pwd']
		pwd2 = request.form['confirm-pwd']

		error = False
		name_error = None
		pwd_error = None
		match_error = None

		query = User.query.filter_by(username=name).all()

		if (len(query) != 0):
			name_error = 'name taken'
			error = True

		if (validate_username(name) == False):
			name_error = 'invalid username'
			error = True

		if (validate_password(pwd1) == False):
			pwd_error = 'invalid password'
			error = True

		if (pwd1 != pwd2):
			match_error = 'passwords do not match'
			error = True

		if (error == True):
			return render_template('nodal_signup.html', title='nodal :: signup',
				name_err=name_error, pwd_err=pwd_error, match_err=match_error)

		else:
			salt = generate_salt(4)
			pwd = hash_password(pwd1, salt)
			user = User(name, pwd, salt)
			db.session.add(user)
			db.session.commit()

			node = Node(user.ID, "ROOT","I am root. [root is the root of all nodes - as such it may not be deleted or modified in any way]")
			db.session.add(node)
			db.session.commit()

			session['user'] = user.ID

			return redirect('/nodal')

	return render_template('nodal_signup.html', title='nodal :: signup')

@app.route('/nodal/logout')
def logout():
	if 'user' in session:
		del session['user']
	return redirect('/nodal/login')

@app.route('/nodal/node')
def viewNode():

	if ('id' in request.args):
		id = request.args.get('id')
		node = Node.query.filter_by(ID=id).first()

		if (node is None):
			return render_template('view-node.html',
				title="nodal :: node :: N/A")

		links = Link.query.filter_by(node1=id).all()
		links += Link.query.filter_by(node2=id).all()
		print(links)
		lonks = []
		for link in links:
			if (link.node1 == int(id)):
				lonks.append(link.node2)
			else:
				lonks.append(link.node1)

		lonks = [Node.query.filter_by(ID=x).first() for x in lonks]
		print(lonks)
		lonks = [x for x in lonks if x.UID == session['user']]
		print(lonks)

		return render_template('view-node.html',
			title="nodal :: node/" + node.name,
			name=node.name,
			content=node.content,
			timestamp=node.timestamp,
			links=lonks)

	return render_template('view-node.html',
		title="nodal :: node :: N/A")

@app.route('/nodal/node/new', methods=['GET', 'POST'])
def newNode():

	if (request.method == 'POST'):
		
		title = request.form['title']
		content = request.form['content']
		conn = request.form['connect']

		error = False
		title_error = None
		conn_error = None

		if (len(title) == 0):
			title_error = "must have title"
			error = True

		title_test = Node.query.filter_by(name=title).first()
		if (title_error is None and title_test is not None):
			title_error = "title taken"
			error = True

		if (len(conn) == 0):
			conn_error = "must connect to node"
			error = True

		conn_node = Node.query.filter_by(name=conn).first()
		print(conn_node)
		print(conn_error)
		if (conn_error is None and conn_node is None):
			conn_error = "node does not exist"
			print(conn_error)
			error = True

		if (error):
			return render_template('new-node.html', title="nodal :: node/new",
				save_title=(title if (title_error is None) else None),
				save_content=content,
				save_conn=(conn if (conn_error is None) else None),
				title_error=title_error,
				conn_error=conn_error)

		node = Node(session['user'], title, content)
		db.session.add(node)
		db.session.commit()
		node.addLink(session['user'], conn_node.ID)

		id = str(node.ID)

		return redirect('/nodal/node?id=' + id)

	return render_template('new-node.html', title="nodal :: node/new")

@app.route('/nodal/node/root')
def rootNode():
	root = Node.query.filter_by(UID=session['user'], name="ROOT").first()
	id = str(root.ID)
	return redirect('/nodal/node?id=' + id)

@app.route('/nodal/link')
def viewLink():
	return render_template('view-link.html', title="nodal :: link/")

@app.route('/nodal/link/new', methods=['GET', 'POST'])
def newLink():

	if (request.method == 'POST'):
		pass

	return render_template('new-link.html', title="nodal :: link/new")

@app.route('/nodal/search', methods=['GET', 'POST'])
def nodalSearch():

	if (request.method == 'POST'):
		pass

	return render_template('nodal-search.html', title="nodal :: search")


# ~~~~~~~~~~~~~~~

if (__name__ == "__main__"):
	app.run(debug=True)