from flask import Flask, request
import os
import requests
import uuid
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

ARQUIVO_PEDIDOS = "pedidos.json"


@app.route("/")
def home():
    return "Servidor funcionando!"


# ===============================
# SALVAR PEDIDO
# ===============================
def salvar_pedido(order_nsu, dados):
    try:
        try:
            with open(ARQUIVO_PEDIDOS, "r") as f:
                pedidos = json.load(f)
        except:
            pedidos = {}

        pedidos[order_nsu] = dados

        with open(ARQUIVO_PEDIDOS, "w") as f:
            json.dump(pedidos, f)

    except Exception as e:
        print("Erro ao salvar pedido:", e)


# ===============================
# BUSCAR PEDIDO
# ===============================
def buscar_pedido(order_nsu):
    try:
        with open(ARQUIVO_PEDIDOS, "r") as f:
            pedidos = json.load(f)

        return pedidos.get(order_nsu)

    except:
        return None


# ===============================
# RECEBE FORMULÁRIO
# ===============================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    print("Dados recebidos:", data)

    nome = data.get("nome")
    email = data.get("email")

    link, order_nsu = criar_pagamento(nome, email)

    salvar_pedido(order_nsu, {
        "nome": nome,
        "email": email
    })

    enviar_email_pagamento(nome, email, link)

    return "OK", 200


# ===============================
# CRIAR PAGAMENTO
# ===============================
def criar_pagamento(nome, email):

    order_nsu = str(uuid.uuid4())

    url = "https://api.infinitepay.io/invoices/public/checkout/links"

    payload = {
        "handle": "feijonut",
        "webhook_url": "https://webhook-nutri-y5bp.onrender.com/pagamento",
        "order_nsu": order_nsu,
        "customer": {
            "name": nome,
            "email": email
        },
        "items": [
            {
                "quantity": 1,
                "price": 100,
                "description": "Produto 7D Desincha"
            }
        ]
    }

    response = requests.post(url, json=payload)

    try:
        data = response.json()
    except:
        print("Erro ao converter resposta:", response.text)
        return None, None

    link = data.get("url")

    return link, order_nsu


# ===============================
# WEBHOOK PAGAMENTO
# ===============================
@app.route("/pagamento", methods=["POST"])
def pagamento():

    data = request.get_json()

    print("Webhook pagamento recebido:", data)

    order_nsu = data.get("order_nsu")

    pedido = buscar_pedido(order_nsu)

    if pedido:
        nome = pedido["nome"]
        email = pedido["email"]

        enviar_email_pdf(nome, email)

    else:
        print("Pedido não encontrado!")

    return {"success": True}, 200


# ===============================
# FUNÇÃO ENVIO EMAIL (GMAIL)
# ===============================
def enviar_email(destino, assunto, html):

    remetente = "lucasfeijorodrigues@gmail.com"
    senha = os.environ.get("egnx temo tczr sbxg")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = remetente
    msg["To"] = destino

    parte_html = MIMEText(html, "html")
    msg.attach(parte_html)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(remetente, senha)
        server.sendmail(remetente, destino, msg.as_string())


# ===============================
# EMAIL PAGAMENTO (COM BOTÃO)
# ===============================
def enviar_email_pagamento(nome, email, link):

    html = f"""
    <html>
    <body style="font-family: Arial;">

        <p>Olá {nome},</p>

        <p>Vi sua solicitação por aqui.</p>

        <p>Para continuar, clique no botão abaixo:</p>

        <p style="text-align: center;">
            <a href="{link}" 
               style="
               background-color:#28a745;
               color:white;
               padding:12px 20px;
               text-decoration:none;
               border-radius:5px;
               display:inline-block;
               font-weight:bold;">
               Continuar
            </a>
        </p>

        <p>Se não foi você, pode ignorar este email.</p>

        <p>Abs,<br>Lucas</p>

    </body>
    </html>
    """

    enviar_email(email, "Sua solicitação", html)


# ===============================
# EMAIL PDF (COM BOTÃO)
# ===============================
def enviar_email_pdf(nome, email):

    link_material = "https://lncimg.lance.com.br/cdn-cgi/image/width=950,quality=75,fit=pad,format=webp/uploads/2024/11/AGIF24082921530730-scaled-aspect-ratio-512-320.jpg"

    html = f"""
    <html>
    <body style="font-family: Arial;">

        <p>Olá {nome},</p>

        <p>Pagamento confirmado 👍</p>

        <p>Clique abaixo para acessar seu material:</p>

        <p style="text-align: center;">
            <a href="{link_material}" 
               style="
               background-color:#007bff;
               color:white;
               padding:12px 20px;
               text-decoration:none;
               border-radius:5px;
               display:inline-block;
               font-weight:bold;">
               Acessar material
            </a>
        </p>

        <p>Qualquer dúvida, pode me responder aqui.</p>

        <p>Lucas</p>

    </body>
    </html>
    """

    enviar_email(email, "Seu material", html)


# ===============================
# START
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
