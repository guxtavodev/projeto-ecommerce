from flask import Blueprint, request, jsonify
from app.models import Produtos, db
import uuid
from azure.storage.blob import BlobServiceClient
import os
from app.routes import products_bp
# Configurações do Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
AZURE_STORAGE_CONTAINER_NAME = "produtos-imagens"

# Inicializar o cliente do Blob Service
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER_NAME)


# Função para fazer upload de imagens para o Azure Blob Storage
def upload_file_to_blob_storage(container_name, file_name, file_data):
    try:
        blob_client = container_client.get_blob_client(file_name)
        blob_client.upload_blob(file_data, overwrite=True)
        return f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{file_name}"
    except Exception as e:
        print(f"Erro ao fazer upload: {e}")
        return None

### Rota para Adicionar Produto
@products_bp.route("/product-add", methods=["POST"])
def add_product():
    data = request.form

    # Supondo que o arquivo de imagem esteja sendo enviado no campo 'imagem' do formulário.
    imagem_file = request.files.get('imagem')
    if imagem_file:
        file_name = f"{data['nome']}_imagem_{uuid.uuid4()}.png"
        imagem_url = upload_file_to_blob_storage(AZURE_STORAGE_CONTAINER_NAME, file_name, imagem_file)
        
        if not imagem_url:
            return jsonify({"msg": "Erro ao fazer upload da imagem"}), 500
    else:
        imagem_url = ""

    # Criação do registro do produto no banco de dados
    produto = Produtos(
        nome=data["nome"],
        id=str(uuid.uuid4()),
        descricao=data["descricao"],
        preco=float(data["preco"]),
        loja=data["loja"],
        categoria=data["categoria"],
        imagem_url=imagem_url,
        especificacoes=data.get("especificacoes", "")
    )
    db.session.add(produto)
    db.session.commit()

    return jsonify({"msg": "Produto adicionado com sucesso", "id": produto.id}), 201

### Rota para Obter um Produto
@products_bp.route("/get-product/<product_id>", methods=["GET"])
def get_product(product_id):
    produto = Produtos.query.filter_by(id=product_id).first()
    if produto:
        return jsonify({
            "id": produto.id,
            "nome": produto.nome,
            "descricao": produto.descricao,
            "preco": produto.preco,
            "loja": produto.loja,
            "categoria": produto.categoria,
            "imagem_url": produto.imagem_url,
            "especificacoes": produto.especificacoes
        }), 200
    else:
        return jsonify({"msg": "Produto não encontrado"}), 404

### Rota para Editar um Produto
@products_bp.route("/edit-product/<product_id>", methods=["PUT"])
def edit_product(product_id):
    data = request.form
    produto = Produtos.query.filter_by(id=product_id).first()
    if produto:
        produto.nome = data.get("nome", produto.nome)
        produto.descricao = data.get("descricao", produto.descricao)
        produto.preco = float(data.get("preco", produto.preco))
        produto.loja = data.get("loja", produto.loja)
        produto.categoria = data.get("categoria", produto.categoria)
        produto.especificacoes = data.get("especificacoes", produto.especificacoes)

        # Se uma nova imagem foi enviada, fazer o upload e atualizar a URL da imagem
        imagem_file = request.files.get('imagem')
        if imagem_file:
            file_name = f"{produto.nome}_imagem_{uuid.uuid4()}.png"
            imagem_url = upload_file_to_blob_storage(AZURE_STORAGE_CONTAINER_NAME, file_name, imagem_file)
            
            if not imagem_url:
                return jsonify({"msg": "Erro ao fazer upload da imagem"}), 500

            produto.imagem_url = imagem_url

        db.session.commit()
        return jsonify({"msg": "Produto atualizado com sucesso"}), 200
    else:
        return jsonify({"msg": "Produto não encontrado"}), 404

### Rota para Deletar um Produto
@products_bp.route("/delete-product/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    produto = Produtos.query.filter_by(id=product_id).first()
    if produto:
        db.session.delete(produto)
        db.session.commit()
        return jsonify({"msg": "Produto deletado com sucesso"}), 200
    else:
        return jsonify({"msg": "Produto não encontrado"}), 404

### Rota para Listar Todos os Produtos
@products_bp.route("/", methods=["GET"])
def list_products():
    produtos = Produtos.query.all()
    produtos_list = [{
        "id": produto.id,
        "nome": produto.nome,
        "descricao": produto.descricao,
        "preco": produto.preco,
        "loja": produto.loja,
        "categoria": produto.categoria,
        "imagem_url": produto.imagem_url,
        "especificacoes": produto.especificacoes
    } for produto in produtos]
    return jsonify(produtos_list), 200

@products_bp.route("/categories", methods=["GET"])
def get_categories():
    categorias = db.session.query(Produtos.categoria).distinct().all()
    categorias_list = [categoria[0] for categoria in categorias]
    
    return jsonify(categorias_list), 200
