from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS
import os
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
CORS(app)
load_dotenv()

ca_path = os.path.join(os.path.dirname(__file__), 'ca.pem')

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Connection arguments
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "ssl_ca": ca_path,
            "ssl_verify_cert": True
        }
    }

login_manager = LoginManager()
login_manager.init_app(app)
app.config.from_object(Config)
db = SQLAlchemy(app)
@app.route('/')
def home():
    return {"message": "Backend is running!"}



@login_manager.user_loader
def load_user(user_id):
    return UserAuth.query.get(int(user_id))

### User Login
@app.post("/login")
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = UserAuth.query.filter_by(email=email).first()
    if user and user.password_hash == password:
        login_user(user)
        return {"message": "Login successful"}
    else:
        return {"error": "Invalid email or password"}, 401

### User Logout
@app.post("/logout")
@login_required
def logout():
    logout_user()
    return {"message": "Logout successful"}

# ### Adding a meal plan
# ### If the plan does not exist, 404
# @app.get("/meal_plan_sub/<int:plan_id>")
# def meal_plan_sub(plan_id):
#     plan = query_one("SELECT * FROM meal_plans WHERE id = %s", (plan_id,))
#     if not plan:
#         return {"error": "Plan not found"}, 404
#     command = execute("INSERT INTO customer (meal_plan_id) VALUES (%s)", (plan_id,))
#     if not command:
#         return {"error": "Failed to subscribe to plan"}, 500

#     return {"message": "Successfully subscribed to plan"}

# ### Adding a workout plan
# ### If the plan does not exist, 404
# @app.get("/workout_plan_sub/<int:plan_id>")
# def workout_plan_sub(plan_id):
#     plan = query_one("SELECT * FROM workout_plans WHERE id = %s", (plan_id,))
#     if not plan:
#         return {"error": "Plan not found"}, 404
#     command = execute("INSERT INTO customer (workout_plan_id) VALUES (%s)", (plan_id,))
#     if not command:
#         return {"error": "Failed to subscribe to plan"}, 500

#     return {"message": "Successfully subscribed to plan"}


# ### Adding a Coach
# ### If the coach does not exist, 404
# @app.get("/coach_sub/<int:coach_id>")
# def coach_sub(coach_id):
#     coach = query_one("SELECT * FROM coaches WHERE id = %s", (coach_id,))
#     if not coach:
#         return {"error": "Coach not found"}, 404
#     command = execute("INSERT INTO customer (coach_id) VALUES (%s)", (coach_id,))
#     if not command:
#         return {"error": "Failed to subscribe to coach"}, 500

#     return {"message": "Successfully subscribed to coach"}

# ### Updating name

# ### Updating user information
# ### First Name, Last Name, Email, Password
# ### Old version
# """
# @app.put("/clientedit/<int:client_id>")
# def client_edit(client_id):
#     data = request.get_json()
#     first_name = data.get("first_name")
#     last_name = data.get("last_name")
#     new_email = data.get("email")
#     new_pass = data.get("password")
#     if not first_name and not last_name and not new_email and not new_pass:
#         return {"error": "No data provided"}, 400

#     fields = []
#     params = []
#     if first_name:
#         fields.append("first_name = %s")
#         params.append(first_name)
#     if last_name:
#         fields.append("last_name = %s")
#         params.append(last_name)
#     if email:
#         fields.append("email = %s")
#         params.append(email)
#     params.append(customer_id)
#     command = execute(sql, (new_email, client_id))

#     if not command:
#         return {"error": "Failed to update email"}, 500
#     return {"status": "updated", "customer_id": customer_id}
# """

# ### Updating user information
# ### First Name, Last Name, Email, Password
# @app.put("/clientedit/<int:client_id>")
# def client_edit(client_id):
#     data = request.get_json()
#     updates = {key: value for key, value in data.items() if value is not None}
#     if not updates:
#         return {"error": "No data provided"}, 400
    
#     command = db.session.query(Customer).filter_by(id=client_id).update(updates)
#     if not command:
#         return {"error": "Failed to update client information"}, 500
#     db.session.commit()
#     return {"status": "updated", "customer_id": client_id}


# ### Log daily calories
# ### Insert a number of calories for the day
# ### this code is reused for several daily logs
# @app.get("/log_calories/<int:calories>")
# def log_calories(calories):
#     command = execute("INSERT INTO daily_cals (calorie_count) VALUES (%s)", (calories,))
#     if not command:
#         return {"error": "Failed to log calories"}, 500

#     return {"message": "Successfully logged calories"}

# ### Log daily steps taken
# app.put("/log_steps/<int:steps>")
# def log_steps(steps):
#     command = execute("INSERT INTO daily_steps (step_count) VALUES (%s)", (steps,))
#     if not command:
#         return {"error": "Failed to log steps"}, 500

#     return {"message": "Successfully logged steps"}

if __name__ == "__main__":
    app.run(debug=True)