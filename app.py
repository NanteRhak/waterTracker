from flask import Flask, render_template, redirect, url_for, session, flash
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from datetime import datetime, date, timedelta
import pytz
import os
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
app.config['BOOTSTRAP_SERVE_LOCAL'] = True

# ✅ Configuration timezone forcé Madagascar
MADAGASCAR_TIMEZONE = pytz.timezone('Indian/Antananarivo')
os.environ['TZ'] = 'Indian/Antananarivo'
time.tzset()

bootstrap = Bootstrap5(app)

class WaterIntake(FlaskForm):
    quantity = DecimalField('Quantité', validators=[DataRequired(), NumberRange(min=0.1)])
    unit = SelectField('Type', choices=[('mL','mL'),('verre (250 mL)','verre (250 mL)')])
    submit = SubmitField('Ajouter')

class SetGoal(FlaskForm):
    goal = DecimalField('Entrer ici votre objectif', validators=[DataRequired(), NumberRange(min=0.1)])
    submit = SubmitField('Enregistrer')

def get_madagascar_time():
    """Retourne la date/heure actuelle à Madagascar"""
    return datetime.now(MADAGASCAR_TIMEZONE)

def get_madagascar_today():
    """Retourne la date du jour à Madagascar"""
    return get_madagascar_time().date()

def format_madagascar_datetime(dt=None):
    """Formate une datetime dans le timezone de Madagascar"""
    if dt is None:
        dt = get_madagascar_time()
    
    if dt.tzinfo is None:
        # Si naive, convertir au timezone Madagascar
        dt = MADAGASCAR_TIMEZONE.localize(dt)
    
    return {
        'date': dt.strftime("%d-%m-%Y"),
        'time': dt.strftime("%H:%M"),
        'iso': dt.isoformat()
    }

def init_session():
    if 'current_total' not in session:
        session['current_total'] = 0
    if 'history' not in session:
        session['history'] = []
    if 'goal' not in session:
        session['goal'] = 2000
    if 'last_reset_date' not in session:
        madagascar_today = get_madagascar_today().isoformat()
        session['last_reset_date'] = madagascar_today
    if 'last_consumption_time' not in session:
        session['last_consumption_time'] = get_madagascar_time().isoformat()

def check_daily_reset():
    """Vérifie et réinitialise seulement le total quotidien, pas l'historique (selon heure Madagascar)"""
    madagascar_today = get_madagascar_today().isoformat()
    
    if session.get('last_reset_date') != madagascar_today:
        # ✅ Nouveau jour - réinitialiser seulement le total quotidien (selon Madagascar)
        session['current_total'] = 0
        session['last_reset_date'] = madagascar_today
        session['last_consumption_time'] = get_madagascar_time().isoformat()  # Reset du timer
        session.modified = True
        print(f"✅ Total quotidien réinitialisé pour le {madagascar_today} (timezone: Madagascar)")

def convert_to_ml(quantity, unit):
    if unit == 'verre (250 mL)':
        return quantity * 250
    return quantity

def check_water_reminder():
    """Vérifie si l'utilisateur n'a pas bu d'eau depuis 2 heures (selon heure Madagascar)"""
    if 'last_consumption_time' not in session:
        return False
    
    try:
        # Convertir le timestamp stocké en datetime avec timezone Madagascar
        last_time = datetime.fromisoformat(session['last_consumption_time'])
        if last_time.tzinfo is None:
            # Si naive, ajouter le timezone Madagascar
            last_time = MADAGASCAR_TIMEZONE.localize(last_time)
        
        now = get_madagascar_time()
        time_diff = now - last_time
        
        # ✅ Vérifier si 2 heures se sont écoulées
        if time_diff.total_seconds() >= 7200:  # 2 heures en secondes
            return True
    except (ValueError, TypeError) as e:
        print(f"❌ Erreur lors de la vérification du rappel: {e}")
    
    return False

def get_weekly_consumption():
    """Calcule la consommation pour les 7 derniers jours (lundi à dimanche) selon l'heure Madagascar"""
    weekly_data = {
        'labels': [],  # Jours de la semaine
        'data': [],    # Consommation en mL
        'colors': []   # Couleurs pour le graphique
    }
    
    # Obtenir le lundi de cette semaine selon l'heure Madagascar
    madagascar_today = get_madagascar_today()
    start_of_week = madagascar_today - timedelta(days=madagascar_today.weekday())  # Lundi
    
    # Générer les 7 jours de la semaine (lundi à dimanche)
    for i in range(7):
        current_day = start_of_week + timedelta(days=i)
        day_label = current_day.strftime("%a")  # Nom court du jour
        date_str_fr = current_day.strftime("%d-%m-%Y")  # Format français pour la comparaison
        
        # Calculer la consommation pour ce jour
        daily_total = 0
        for entry in session.get('history', []):
            if entry['date'] == date_str_fr:
                daily_total += entry['quantity_ml']
        
        weekly_data['labels'].append(day_label)
        weekly_data['data'].append(daily_total)
        
        # Définir la couleur (verte si objectif atteint, bleue sinon)
        goal = session.get('goal', 2000)
        color = 'rgba(75, 192, 75, 0.7)' if daily_total >= goal else 'rgba(54, 162, 235, 0.7)'
        weekly_data['colors'].append(color)
    
    return weekly_data

def cleanup_old_history():
    """Nettoie l'historique pour garder seulement les 30 derniers jours (selon heure Madagascar)"""
    if 'history' not in session:
        return
    
    madagascar_today = get_madagascar_today()
    thirty_days_ago = madagascar_today - timedelta(days=30)
    cleaned_history = []
    
    for entry in session['history']:
        try:
            # Convertir la date stockée en objet date
            entry_date = datetime.strptime(entry['date'], "%d-%m-%Y").date()
            # Garder seulement les entrées des 30 derniers jours
            if entry_date >= thirty_days_ago:
                cleaned_history.append(entry)
        except ValueError:
            # Si le format de date est invalide, garder l'entrée
            cleaned_history.append(entry)
    
    # Mettre à jour l'historique seulement si des entrées ont été supprimées
    if len(cleaned_history) != len(session['history']):
        session['history'] = cleaned_history
        session.modified = True

@app.route('/', methods=['GET','POST'])
def index():
    init_session()
    check_daily_reset()
    cleanup_old_history()
    form = WaterIntake()

    goal = session.get('goal', 2000)
    current_total = session.get('current_total', 0)
    percentage = min((current_total / goal) * 100, 100) if goal > 0 else 0
    
    # ✅ Vérifier si une notification est nécessaire (selon heure Madagascar)
    needs_reminder = check_water_reminder()
    
    # ✅ Obtenir les données hebdomadaires pour l'histogramme
    weekly_data = get_weekly_consumption()
    
    if form.validate_on_submit():
        quantity = float(form.quantity.data)
        unit = form.unit.data
        quantity_ml = convert_to_ml(quantity, unit)

        # ✅ Utiliser l'heure de Madagascar pour l'horodatage
        madagascar_datetime = format_madagascar_datetime()
        
        entry = {
            'quantity': quantity,
            'unit': unit,
            'date': madagascar_datetime['date'],
            'time': madagascar_datetime['time'],
            'quantity_ml': quantity_ml,
            'total_after': session['current_total'] + quantity_ml
        }

        session['current_total'] += quantity_ml
        session['history'].append(entry)
        # ✅ Mettre à jour le timestamp de la dernière consommation avec timezone Madagascar
        session['last_consumption_time'] = madagascar_datetime['iso']
        session.modified = True
        
        flash(f'{quantity} {unit} ajouté. Total: {session["current_total"]} mL', 'success')
        return redirect(url_for('index'))

    return render_template('index.html', 
                         form=form, 
                         progress=percentage, 
                         current_total=current_total, 
                         goal=goal,
                         weekly_data=weekly_data,
                         needs_reminder=needs_reminder)

@app.route('/history')
def history():
    init_session()
    check_daily_reset()
    cleanup_old_history()
    history_data = session.get('history', [])
    
    # ✅ Vérifier si une notification est nécessaire
    needs_reminder = check_water_reminder()
    
    # Trier l'historique par date et heure (plus récent en premier)
    history_data.sort(key=lambda x: datetime.strptime(x['date'] + ' ' + x['time'], "%d-%m-%Y %H:%M"), reverse=True)
    
    return render_template('history.html', history=history_data, needs_reminder=needs_reminder)

@app.route('/settings', methods=['GET','POST'])
def settings():
    init_session()
    check_daily_reset()
    cleanup_old_history()
    set_goal = SetGoal()

    # ✅ Vérifier si une notification est nécessaire
    needs_reminder = check_water_reminder()

    if set_goal.validate_on_submit():
        goal = float(set_goal.goal.data)
        session['goal'] = goal
        session.modified = True
        flash(f'Nouvel objectif défini: {goal} mL', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', set_goal=set_goal, goal=session.get('goal'), needs_reminder=needs_reminder)

@app.route('/reset')
def reset_progress():
    init_session()
    check_daily_reset()
    
    # Réinitialiser seulement le total du jour, pas l'historique complet
    session['current_total'] = 0
    # ✅ Reset du timer de consommation avec timezone Madagascar
    session['last_consumption_time'] = get_madagascar_time().isoformat()
    session.modified = True
    flash("Votre consommation du jour a été réinitialisée", "success")
    return redirect(url_for('settings'))

@app.route('/clear_history')
def clear_history():
    """Route optionnelle pour vider complètement l'historique"""
    init_session()
    session['history'] = []
    session.modified = True
    flash("Historique complètement effacé", "info")
    return redirect(url_for('history'))

if __name__ == '__main__':
    app.run(debug=True, port=2527)
