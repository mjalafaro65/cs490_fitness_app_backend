from flask import Flask, render_template, request, jsonify
from datetime import datetime
from flask_cors import CORS
from db import db
import os
from dotenv import load_dotenv
from flask_smorest import Api, Blueprint
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required
from flask_migrate import Migrate
from db import db  # This replaces your 'db = SQLAlchemy(app)' line later
from middleware import roles_required
from schemas.auth_schema import RegisterSchema
from features.auth import auth_blp
from features.coaching import coach_blp
from features.admin import admin_blp
from features.client import client_blp
from features.workouts import workout_blp
from features.notifications import notif_blp
from features.messaging import messaging_blp
from features.socketio_events import socketio
from features.user import user_blp

load_dotenv()

ca_path = os.path.join(os.path.dirname(__file__), 'ca.pem')

##Set up config class 
class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    #Connection arguments
    # SQLALCHEMY_ENGINE_OPTIONS = {
    #     "connect_args": {
    #         "ssl_ca": ca_path,
    #         "ssl_verify_cert": True
    #     }
    # }

    ## swagger configuration 
    API_TITLE = "Fitness Project API"
    API_VERSION= "v1"
    OPENAPI_VERSION= "3.0.3"
    OPENAPI_URL_PREFIX = ""
    OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    API_SPEC_OPTIONS = {
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        },
        "security": [{"bearerAuth": []}]
    }

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)

db.init_app(app)
migrate = Migrate(app, db)


#int api
api = Api(app)

app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY", "dev-secret-key") 
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # Tokens never expire for development
jwt = JWTManager(app)

# Initialize SocketIO with the app
socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')

#register blueprints
api.register_blueprint(auth_blp)
api.register_blueprint(client_blp)
api.register_blueprint(coach_blp)
api.register_blueprint(workout_blp)
api.register_blueprint(admin_blp)
api.register_blueprint(notif_blp)
api.register_blueprint(messaging_blp)
api.register_blueprint(user_blp)



@app.route('/')
def home():
    return {"message": "Backend is running!"}

# # AUTHENTICATION
# @app.route('/register', methods=['POST'])
# def signup():
#     schema = RegisterSchema()
#     errors = schema.validate(request.json)
#     if errors:
#         return jsonify(errors), 400
#     result, status = register_user(request.json)
#     return jsonify(result), status

# @app.route('/me', methods=['GET'])
# @jwt_required()
# def get_profile():
#     current_user_id = get_jwt_identity()
#     return jsonify({
#         "logged_in_as": current_user_id,
#         "message": "Token is valid and middleware is active"
#     }), 200

# @app.route('/login', methods=['POST'])
# def signin():
#     result, status = login_user(request.json)
#     return jsonify(result), status

# # ROLE BASED ACCESS CONTROL
# @app.route('/admin/promote/<int:auth_id>', methods=['POST'])
# @roles_required('admin')
# def admin_promote(auth_id):
#     result, status = promote_to_coach(auth_id)
#     return jsonify(result), status

# Client

# @login_manager.user_loader
# def load_user(user_id):
#     return UserAuth.query.get(int(user_id))


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
    
    # with app.app_context():
    #     import models
    #     # sync model to database before app start
    #     db.create_all() 
    
    socketio.run(app, debug=True)