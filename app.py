from flask import Flask, request
import os
import requests
import uuid
import json
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

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
# RECEBE DADOS DO FORMULÁRIO
# ===============================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    print("Dados recebidos:", data)

    nome = data.get("nome")
    email = data.get("email")

    # Criar pagamento na InfinitePay
    link, order_nsu = criar_pagamento(nome, email)

    # Salvar pedido em arquivo
    salvar_pedido(order_nsu, {
        "nome": nome,
        "email": email
    })

    # Enviar email com link de pagamento
    enviar_email_pagamento(nome, email, link)

    return "OK", 200


# ===============================
# CRIA PAGAMENTO NA INFINITEPAY
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
                "price": 1,
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

    print("Resposta InfinitePay:", data)

    link = data.get("url")

    return link, order_nsu


# ===============================
# WEBHOOK DE PAGAMENTO CONFIRMADO
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

        print("Pagamento confirmado para:", email)

        enviar_email_pdf(nome, email)

    else:
        print("Pedido não encontrado!")

    return {"success": True}, 200


# ===============================
# EMAIL COM LINK DE PAGAMENTO
# ===============================
def enviar_email_pagamento(nome, email, link):

    try:
        message = Mail(
            from_email='lucasfeijorodrigues@gmail.com',
            to_emails=email,
            subject='Link para finalizar sua solicitação',
            plain_text_content=f"""
Olá {nome},

Recebemos sua solicitação.

Para continuar, acesse o link abaixo e finalize:

{link}

Se tiver qualquer dúvida, pode responder este email.

Obrigado!
""",
            html_content=f"""
<p>Olá {nome},</p>

<p>Recebemos sua solicitação.</p>

<p>Para continuar, acesse o link abaixo:</p>

<p>{link}</p>

<p>Se tiver qualquer dúvida, pode responder este email.</p>

<p>Obrigado!</p>
"""
        )

        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)

        print("Email pagamento enviado:", response.status_code)

    except Exception as e:
        print("Erro ao enviar email pagamento:", str(e))


# ===============================
# EMAIL COM PDF (APÓS PAGAMENTO)
# ===============================
def enviar_email_pdf(nome, email):

    try:
        message = Mail(
            from_email='lucasfeijorodrigues@gmail.com',
            to_emails=email,
            subject='Seu material solicitado',
            plain_text_content=f"""
Olá {nome},

Pagamento confirmado.

Aqui está seu material:
https://lncimg.lance.com.br/cdn-cgi/image/width=950,quality=75,fit=pad,format=webp/uploads/2024/11/AGIF24082921530730-scaled-aspect-ratio-512-320.jpg

Qualquer dúvida, estou à disposição.
""",
            html_content=f"""
<p>Olá {nome},</p>

<p>Pagamento confirmado.</p>

<p>Aqui está seu material:</p>

<p>
https://lncimg.lance.com.br/cdn-cgi/image/width=950,quality=75,fit=pad,format=webp/uploads/2024/11/AGIF24082921530730-scaled-aspect-ratio-512-320.jpg
</p>

<p>Qualquer dúvida, estou à disposição.</p>
"""
        )

        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)

        print("Email PDF enviado:", response.status_code)

    except Exception as e:
        print("Erro ao enviar PDF:", str(e))


# ===============================
# INICIAR SERVIDOR
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
