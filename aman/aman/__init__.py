"""
The flask application package.
"""

from flask import Flask
app = Flask(__name__)
app.secret_key='super_secret-key'
import aman.views

