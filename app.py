from flask import Flask, render_template, redirect, url_for, session, flash
from flask_bootstrap import Bootstrap5
from config import *
from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
bootstrap = Bootstrap5(app)

class WaterIntake(FlaskForm):
    quantity = DecimalField('Quantité', validators=[DataRequired(), NumberRange(min=0.1)])
    unit = SelectField('Type',choices=[('mL','mL'),('verre','verre')])
    submit = SubmitField('Ajouter')

class SetGoal(FlaskForm):
    goal = DecimalField('Entrer ici votre objéctif', validators=[DataRequired(), NumberRange(min=0.1)])
    submit = SubmitField('Enregistrer')

def init_session():
    if 'current_total' not in session:
        session['current_total'] = 0
    if 'history' not in session:
        session['history'] = []

    if 'goal' not in session:
        session['goal'] = 2000

def convert_to_ml(quantity, unit):
    if unit == 'verre':
        return quantity * 250
    return quantity

@app.route('/', methods=['GET','POST'])
def index():
    init_session()

    form = WaterIntake()
    if form.validate_on_submit():
        quantity = float(form.quantity.data)
        unit = form.unit.data
        quantity_ml = convert_to_ml(quantity, unit)

        entry = {
                    'quantity': quantity,
                    'unit': unit,
                    'quantity_ml': quantity_ml,
                    'total_after': session['current_total']
                }

        session['current_total'] += quantity_ml
        session['history'].append(entry)
        return redirect(url_for('index'))
        session.modified = True
        flash(f'{quantity} {unit} ajouté\n Total: {session["current_total"]} mL', 'success')
        return redirect(url_for('index'))

    return render_template('index.html',form=form,quantity=session.get('quantity'), unit=session.get('unit'))

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/settings',methods=['GET','POST'])
def settings():
    init_session()

    set_goal = SetGoal()
    if set_goal.validate_on_submit():
        goal = float(set_goal.goal.data)
        flash(f'Nouvel objectif défini: {goal} mL', 'success')
        session.modified = True
    return render_template('settings.html',set_goal=set_goal,  goal=session.get('goal'))

if __name__ == '__main__':
    app.run(debug=True, port=2527)
