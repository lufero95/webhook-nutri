from flask import Flask, request
import os
import requests
import uuid
import json
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email

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
# WEBHOOK FORMULÁRIO
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
        print("Erro:", response.text)
        return None, None

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
# EMAIL PAGAMENTO
# ===============================
def enviar_email_pagamento(nome, email, link):

    texto = f"""
Olá {nome},

Vi sua solicitação por aqui.

Para continuar, acesse:
{link}

Se não foi você, pode ignorar este email.

Lucas
"""

    html = f"""
<p>Olá {nome},</p>

<p>Vi sua solicitação por aqui.</p>

<p>Para continuar, clique abaixo:</p>

<p style="text-align:center;">
    <a href="{link}" 
    style="background:#28a745;color:white;padding:12px 20px;
    text-decoration:none;border-radius:5px;font-weight:bold;">
    Ver detalhes
    </a>
</p>

<p>Se preferir, copie e cole este link no navegador:</p>
<p>{link}</p>

<p>Se não foi você, pode ignorar.</p>

<p>Lucas</p>
"""

    enviar_email(email, "Sua solicitação", texto, html)


# ===============================
# EMAIL PDF
# ===============================
def enviar_email_pdf(nome, email):

    link_material = "https://lncimg.lance.com.br/cdn-cgi/image/width=950,quality=75,fit=pad,format=webp/uploads/2024/11/AGIF24082921530730-scaled-aspect-ratio-512-320.jpg"

    texto = f"""
Olá {nome},

Seu acesso já está disponível.

Link:
{link_material}

Qualquer dúvida, pode responder este email.

Lucas
"""

    html = f"""
<p>Olá {nome},</p>

<p>Seu acesso já está disponível.</p>

<p style="text-align:center;">
    <a href="{link_material}" 
    style="background:#007bff;color:white;padding:12px 20px;
    text-decoration:none;border-radius:5px;font-weight:bold;">
    Abrir conteúdo
    </a>
</p>

<p>Se preferir, copie e cole:</p>
<p>{link_material}</p>

<p>Qualquer dúvida, pode responder este email.</p>

<p>Lucas</p>
"""

    enviar_email(email, "Seu acesso", texto, html)


# ===============================
# ENVIO COM SENDGRID
# ===============================
def enviar_email(destino, assunto, texto, html):

    try:
        message = Mail(
            from_email=Email("lucasfeijorodrigues@gmail.com"),
            to_emails=destino,
            subject=assunto,
            plain_text_content=texto,
            html_content=html
        )

        message.reply_to = "lucasfeijorodrigues@gmail.com"

        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)

        print("Email enviado:", response.status_code)

    except Exception as e:
        print("Erro ao enviar email:", str(e))


# ===============================
# START
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
