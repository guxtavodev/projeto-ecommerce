from app import db, app

class Lojas(db.Model):
  nome = db.Column(db.String())
  id = db.Column(db.String(), primary_key=True)
  email = db.Column(db.String())
  telefone = db.Column(db.String())
  endereco = db.Column(db.String())
  logo_url = db.Column(db.String())

  def __init__(self, nome, id, email, telefone, endereco, logo_url):
    self.nome = nome
    self.id = id 
    self.email = email 
    self.telefone = telefone
    self.endereco = endereco 
    self.logo_url = logo_url

class Produtos(db.Model):
  nome = db.Column(db.String())
  id = db.Column(db.String(), primary_key=True)
  descricao = db.Column(db.String())
  preco = db.Column(db.Float())
  loja = db.Column(db.String())
  categoria = db.Column(db.String())
  imagem_url = db.Column(db.String())
  especificacoes = db.Column(db.String())

  def __init__(self, nome, id, descricao, preco, loja, categoria, imagem_url, especificacoes):
    self.nome = nome 
    self.id = id 
    self.descricao = descricao
    self.preco = preco 
    self.loja = loja 
    self.categoria = categoria 
    self.imagem_url = imagem_url
    self.especificacoes = especificacoes

with app.app_context():
  db.create_all()