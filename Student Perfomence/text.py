import joblib
from sklearn import set_config

# Load original model
model = joblib.load('student_grade_predictor.pkl')

# Ensure transform output is default
set_config(transform_output='default')

# Resave model
joblib.dump(model, 'student_grade_predictor_fixed.pkl')
