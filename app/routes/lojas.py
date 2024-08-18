from flask import render_template, redirect, session, jsonify, request, make_response, send_file
from app.routes import lojas_bp
from app.models import Lojas
from app import db
from passlib.hash import bcrypt_sha256
import uuid
import markdown
from azure.storage.blob import BlobServiceClient
import os
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
import re

# Função para fazer o upload de arquivo para o Azure Blob Storage
def upload_file_to_blob_storage(container_name, file_name, file_data):
    try:
        # Conecte-se à sua conta de armazenamento do Azure
        blob_service_client = BlobServiceClient.from_connection_string(os.environ['CONECTION'])

        # Conecte-se ao contêiner de armazenamento ou crie um novo se não existir
        container_client = blob_service_client.get_container_client(container_name)

        try:
            container_client.create_container()
        except ResourceExistsError:
            print("O contêiner já existe.")

        # Enviar arquivo para o Blob Storage
        blob_client = container_client.get_blob_client(file_name)
        blob_client.upload_blob(file_data)
        return True
    except Exception as e:
        print(f"Ocorreu um erro durante o upload do arquivo: {e}")
        return False

# Função para baixar arquivo do Azure Blob Storage
def download_file_from_blob_storage(container_name, blob_name):
    try:
        # Conecte-se à sua conta de armazenamento do Azure
        blob_service_client = BlobServiceClient.from_connection_string(os.environ['CONECTION'])

        # Conecte-se ao contêiner de armazenamento
        container_client = blob_service_client.get_container_client(container_name)

        # Baixe o arquivo do Blob Storage
        blob_client = container_client.get_blob_client(blob_name)
        file_data = blob_client.download_blob().readall()
        return file_data
    except ResourceNotFoundError:
        print("O blob não foi encontrado.")
        return None
    except Exception as e:
        print(f"Ocorreu um erro durante o download do arquivo: {e}")
        return None



@lojas_bp.route("/")
def hello_world():
  return "Servidor funcionando perfeitamente!"

@lojas_bp.route("/create-shop", methods=["POST"])
def createShop():
    data = request.get_json()

    # Supondo que o arquivo de logo esteja sendo enviado no campo 'logo' do formulário.
    logo_file = request.files.get('logo')
    if logo_file:
        # Nome do arquivo para ser armazenado no Azure Blob Storage
        file_name = f"{data['nome']}_logo_{uuid.uuid4()}.png"
        container_name = "lojas-logos"

        # Upload da logo para o Azure Blob Storage
        upload_successful = upload_file_to_blob_storage(container_name, file_name, logo_file)

        if upload_successful:
            # Construir a URL da logo
            logo_url = f"https://guxtacloud.blob.core.windows.net/{container_name}/{file_name}"
        else:
            return jsonify({"msg": "Error uploading logo"}), 500
    else:
        logo_url = ""

    # Criação do registro da loja no banco de dados
    loja = Lojas(
        nome=data["nome"],
        id=str(uuid.uuid4()),
        email=data["email"],
        telefone=data["telefone"],
        endereco=data["endereco"],
        logo_url=logo_url
    )
    db.session.add(loja)
    db.session.commit()

    return jsonify({
        "msg": "success",
        "logo_url": logo_url
    })

@lojas_bp.route("/get-shop/<shop_id>", methods=["GET"])
def getShop(shop_id):
    loja = Lojas.query.filter_by(id=shop_id).first()
    if loja:
        return jsonify({
            "id": loja.id,
            "nome": loja.nome,
            "email": loja.email,
            "telefone": loja.telefone,
            "endereco": loja.endereco,
            "logo_url": loja.logo_url
        }), 200
    else:
        return jsonify({"msg": "Loja não encontrada"}), 404

@lojas_bp.route("/delete-shop/<shop_id>", methods=["DELETE"])
def deleteShop(shop_id):
    loja = Lojas.query.filter_by(id=shop_id).first()
    if loja:
        db.session.delete(loja)
        db.session.commit()
        return jsonify({"msg": "Loja deletada com sucesso"}), 200
    else:
        return jsonify({"msg": "Loja não encontrada"}), 404

@lojas_bp.route("/edit-shop/<shop_id>", methods=["PUT"])
def editShop(shop_id):
    data = request.get_json()
    loja = Lojas.query.filter_by(id=shop_id).first()
    if loja:
        loja.nome = data.get("nome", loja.nome)
        loja.email = data.get("email", loja.email)
        loja.telefone = data.get("telefone", loja.telefone)
        loja.endereco = data.get("endereco", loja.endereco)

        # Se o campo de logo foi enviado, fazer o upload e atualizar o logo_url
        logo_file = request.files.get('logo')
        if logo_file:
            file_name = f"{loja.nome}_logo_{uuid.uuid4()}.png"
            container_name = "lojas-logos"
            upload_successful = upload_file_to_blob_storage(container_name, file_name, logo_file)
            if upload_successful:
                logo_url = f"https://guxtacloud.blob.core.windows.net/{container_name}/{file_name}"
                loja.logo_url = logo_url

        db.session.commit()
        return jsonify({"msg": "Loja atualizada com sucesso"}), 200
    else:
        return jsonify({"msg": "Loja não encontrada"}), 404

@lojas_bp.route("/search-shops", methods=["GET"])
def searchShops():
    nome_query = request.args.get('nome', '')
    lojas = Lojas.query.filter(Lojas.nome.ilike(f"%{nome_query}%")).all()
    lojas_list = [{
        "id": loja.id,
        "nome": loja.nome,
        "email": loja.email,
        "telefone": loja.telefone,
        "endereco": loja.endereco,
        "logo_url": loja.logo_url
    } for loja in lojas]
    return jsonify(lojas_list), 200

@lojas_bp.route("/update-shop-logo/<shop_id>", methods=["PUT"])
def updateShopLogo(shop_id):
    loja = Lojas.query.filter_by(id=shop_id).first()
    if loja:
        logo_file = request.files.get('logo')
        if logo_file:
            file_name = f"{loja.nome}_logo_{uuid.uuid4()}.png"
            container_name = "lojas-logos"
            upload_successful = upload_file_to_blob_storage(container_name, file_name, logo_file)
            if upload_successful:
                logo_url = f"https://guxtacloud.blob.core.windows.net/{container_name}/{file_name}"
                loja.logo_url = logo_url
                db.session.commit()
                return jsonify({"msg": "Logo atualizada com sucesso", "logo_url": logo_url}), 200
            else:
                return jsonify({"msg": "Erro ao fazer upload do logo"}), 500
        else:
            return jsonify({"msg": "Logo não fornecida"}), 400
    else:
        return jsonify({"msg": "Loja não encontrada"}), 404
