#!/usr/bin/env python3
"""Point d'entrée du Backoffice HBntory."""
import os

from flask import Flask
from database import db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

db.init_app(app)
