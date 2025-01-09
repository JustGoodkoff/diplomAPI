from flask import Flask
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

bcrypt = Bcrypt(app)
jwt = JWTManager(app)