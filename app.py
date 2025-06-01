from flask import Flask
import os
import config
from config import LocalDevelopmentConfig
from database import db
from controllers.controllers import main
from flask_login import LoginManager

from models.models import User

def create_app():
    app = Flask(__name__, template_folder="templates")
    
    if os.getenv('ENV', 'development') != "production":
        print("Starting Local Development")
        app.config.from_object(LocalDevelopmentConfig)
        
    else:
        raise Exception("Currently no production config is setup")

    app.register_blueprint(main)
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.login_view = "main.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app

app = create_app()

if __name__ == "__main__":
    app.debug = True
    app.run(port=5001)
