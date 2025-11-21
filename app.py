from flask import Flask, render_template, redirect, url_for, session, flash
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from datetime import datetime, date

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
bootstrap = Bootstrap5(app)

class WaterIntake(FlaskForm):
    quantity = DecimalField('Quantité', validators=[DataRequired(), NumberRange(min=0.1)])
    unit = SelectField('Type', choices=[('mL','mL'),('verre','verre')])
    submit = SubmitField('Ajouter')

class SetGoal(FlaskForm):
    goal = DecimalField('Entrer ici votre objectif', validators=[DataRequired(), NumberRange(min=0.1)])
    submit = SubmitField('Enregistrer')

def init_session():
    if 'current_total' not in session:
        session['current_total'] = 0
    if 'history' not in session:
        session['history'] = []
    if 'goal' not in session:
        session['goal'] = 2000
    if 'last_reset_date' not in session:
        session['last_reset_date'] = date.today().isoformat()

def check_daily_reset():
    """Vérifie et réinitialise si un nouveau jour commence"""
    today = date.today().isoformat()
    
    if session.get('last_reset_date') != today:
        # Nouveau jour - réinitialiser
        session['current_total'] = 0
        session['history'] = []
        session['last_reset_date'] = today
        session.modified = True
        print(f"✅ Historique réinitialisé pour le {today}")

def convert_to_ml(quantity, unit):
    if unit == 'verre':
        return quantity * 250
    return quantity

@app.route('/', methods=['GET','POST'])
def index():
    init_session()
    check_daily_reset()
    form = WaterIntake()

    goal = session.get('goal', 2000)
    current_total = session.get('current_total', 0)
    percentage = min((current_total / goal) * 100, 100) if goal > 0 else 0
    
    if form.validate_on_submit():
        quantity = float(form.quantity.data)
        unit = form.unit.data
        quantity_ml = convert_to_ml(quantity, unit)

        entry = {
            'quantity': quantity,
            'unit': unit,
            'date': datetime.now().strftime("%d-%m-%Y"),
            'time': datetime.now().strftime("%H:%M"),
            'quantity_ml': quantity_ml,
            'total_after': session['current_total'] + quantity_ml
        }

        session['current_total'] += quantity_ml
        session['history'].append(entry)
        session.modified = True
        
        flash(f'{quantity} {unit} ajouté. Total: {session["current_total"]} mL', 'success')
        return redirect(url_for('index'))

    return render_template('index.html', form=form, progress=percentage, current_total=current_total, goal=goal)

@app.route('/history')
def history():
    init_session()
    check_daily_reset()
    history_data = session.get('history', [])
    return render_template('history.html', history=history_data)

@app.route('/settings', methods=['GET','POST'])
def settings():
    init_session()
    check_daily_reset()
    set_goal = SetGoal()

    if set_goal.validate_on_submit():
        goal = float(set_goal.goal.data)
        session['goal'] = goal
        session.modified = True
        flash(f'Nouvel objectif défini: {goal} mL', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', set_goal=set_goal, goal=session.get('goal'))

@app.route('/reset')
def reset_progress():
    init_session()
    check_daily_reset()
    
    session['current_total'] = 0
    session['history'] = []
    session.modified = True
    flash("Votre consommation du jour a été réinitialisée", "success")
    return redirect(url_for('settings'))

if __name__ == '__main__':
    app.run(debug=True, port=2527)
