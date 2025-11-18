from flask import Flask, render_template
from flask_bootstrap import Bootstrap5
from config import *

app = Flask(__name__)
app.secret_key = "very-hard-to-guess"
bootstrap = Bootstrap5(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/settings')
def settings():
   return render_template('settings.html')

if __name__ == '__main__':
    app.run(debug=True, port=2527)
