from flask import Flask, request
import os
import requests
import uuid
import json
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

ARQUIVO_PEDIDOS = "pedidos.json"

EMAIL_REMETENTE = "lucasfeijorodrigues@gmail.com"
SENHA_EMAIL = "egnx temo tczr sbxg"

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

        print("Pedido salvo no arquivo!")

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
# CRIA PAGAMENTO
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
        print("Erro InfinitePay:", response.text)
        return None, None

    print("Resposta InfinitePay:", data)

    return data.get("url"), order_nsu

# ===============================
# WEBHOOK PAGAMENTO
# ===============================
@app.route("/pagamento", methods=["POST"])
def pagamento():

    data = request.get_json()

    print("Pagamento recebido:", data)

    order_nsu = data.get("order_nsu")

    pedido = buscar_pedido(order_nsu)

    if pedido:
        enviar_email_pdf(pedido["nome"], pedido["email"])
    else:
        print("Pedido não encontrado!")

    return {"success": True}, 200

# ===============================
# ENVIO EMAIL (PAGAMENTO)
# ===============================
def enviar_email_pagamento(nome, email, link):

    try:
        msg = MIMEText(f"""
Olá {nome},

Vi aqui que você preencheu o formulário.

Para continuar:
{link}

Se precisar, pode me responder aqui.

Lucas
""")

        msg["Subject"] = "Sua solicitação"
        msg["From"] = EMAIL_REMETENTE
        msg["To"] = email

        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(EMAIL_REMETENTE, SENHA_EMAIL)

        servidor.send_message(msg)
        servidor.quit()

        print("Email pagamento enviado")

    except Exception as e:
        print("Erro email pagamento:", e)

# ===============================
# ENVIO EMAIL (PDF)
# ===============================
def enviar_email_pdf(nome, email):

    try:
        msg = MIMEText(f"""
Olá {nome},

Pagamento confirmado.

Segue o material:
https://lncimg.lance.com.br/cdn-cgi/image/width=950,quality=75,fit=pad,format=webp/uploads/2024/11/AGIF24082921530730-scaled-aspect-ratio-512-320.jpg

Qualquer dúvida, pode responder aqui.

Lucas
""")

        msg["Subject"] = "Seu material"
        msg["From"] = EMAIL_REMETENTE
        msg["To"] = email

        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(EMAIL_REMETENTE, SENHA_EMAIL)

        servidor.send_message(msg)
        servidor.quit()

        print("Email PDF enviado")

    except Exception as e:
        print("Erro email PDF:", e)

# ===============================
# START
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
