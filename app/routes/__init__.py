from flask import Blueprint

lojas_bp = Blueprint('lojas', __name__)

from app.routes import lojas