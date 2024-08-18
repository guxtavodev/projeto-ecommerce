from flask import Blueprint

lojas_bp = Blueprint('lojas', __name__)
products_bp = Blueprint('products', __name__)

from app.routes import lojas, products