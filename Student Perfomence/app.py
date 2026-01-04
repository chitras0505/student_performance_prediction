from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this in production!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Load the trained model
model = joblib.load('student_grade_predictor.pkl')

# --------------- Database Models ---------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    full_name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))


# Optional StudentRecord model (not used for saving predictions)
class StudentRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gender = db.Column(db.String(10))
    race_ethnicity = db.Column(db.String(20))
    parental_level_of_education = db.Column(db.String(50))
    lunch = db.Column(db.String(20))
    test_preparation_course = db.Column(db.String(20))
    math_score = db.Column(db.Integer)
    reading_score = db.Column(db.Integer)
    writing_score = db.Column(db.Integer)
    grade = db.Column(db.String(10))

# --------------- Routes ---------------
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user'] = user.username
            session['user_id'] = user.id  # ✅ Add this line
            return redirect(url_for('dashboard'))
        return render_template('login.html', error="Invalid Credentials")
    return render_template('login.html')
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    
    if request.method == 'POST':
        existing_user = User.query.filter_by(username=request.form['username']).first()
        if existing_user:
            return render_template('register.html', error="Username already exists")
        hashed_pw = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        new_user = User(
    username=request.form['username'],
    password=hashed_pw,
    full_name=request.form.get('full_name'),
    email=request.form.get('email'),
    phone=request.form.get('phone'),
    address=request.form.get('address')
)

        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if 'user' not in session:
        return redirect(url_for('login'))

    result = None
    data_for_model = None

    if request.method == 'POST':
        # Prepare data dict for model prediction
        data_for_model = {
            'gender': request.form['gender'],
            'race/ethnicity': request.form['race'],
            'parental level of education': request.form['parent_edu'],
            'lunch': request.form['lunch'],
            'test preparation course': request.form['prep'],
            'math score': int(request.form['math']),
            'reading score': int(request.form['reading']),
            'writing score': int(request.form['writing']),
        }

        df = pd.DataFrame([data_for_model])
        prediction = model.predict(df)[0]
        grade_map = {0: 'Fail', 1: 'Grade3', 2: 'Grade2', 3: 'Grade1'}
        result = grade_map.get(prediction, 'Unknown')

        # Not saving prediction to DB as per your request

    return render_template('predict.html', result=result, input_data=data_for_model)

@app.route('/details')
def details():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    current_user = User.query.filter_by(id=session['user_id']).first()
    return render_template('details.html', user=current_user)

@app.route('/model')
def model_info():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('model.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# --------------- Main ---------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
