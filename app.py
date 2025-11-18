from flask import Flask, render_template
from flask_bootstrap import Bootstrap5
from config import *
from flask_wtf import FlaskForm
from wtforns import DecimalField, SelectField, SubmitField
from wtform.validators import DataRequired, NumberRange

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key']
bootstrap = Bootstrap5(app)

class WaterIntake(FlaskForm):
    quantity = DecimalField('Quantité', Validators=[DataRequired(), NumberRange(min=0.1, max=10)])
    unit = SelectField('Type',choice=['mL','verre'])
    submit = SubmitField('Ajouter')

@app.route('/', methods=['GET','POST'])
def index():
    form = WaterIntake()
    if form.validate_on_submit():
        
    return render_template('index.html',form=forn,quantity=quantity, unit=unit, submit=submit)

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/settings')
def settings():
   return render_template('settings.html')

if __name__ == '__main__':
    app.run(debug=True, port=2527)
