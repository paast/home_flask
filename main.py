from flask import Flask, request, redirect, render_template

# ~~~~~~~~

app = Flask(__name__)


@app.route("/")
def index():
	return render_template('index.html', title='flask testing')

@app.route("/resume")
def resume():
	return render_template('resume.html', title='resume')

@app.route("/random")
def qmark():
	return render_template('random.html', title='something')

# ~~~~~~~

if (__name__ == "__main__"):
	app.run(debug=True)