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
SENHA_EMAIL = "SUA_SENHA_DE_APP_AQUI"

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

        print("✅ Pedido salvo no arquivo!")

    except Exception as e:
        print("❌ Erro ao salvar pedido:", e)

# ===============================
# BUSCAR PEDIDO
# ===============================
def buscar_pedido(order_nsu):
    try:
        with open(ARQUIVO_PEDIDOS, "r") as f:
            pedidos = json.load(f)

        return pedidos.get(order_nsu)

    except Exception as e:
        print("❌ Erro ao buscar pedido:", e)
        return None

# ===============================
# WEBHOOK FORMULÁRIO
# ===============================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()

        print("\n=== 🚀 WEBHOOK RECEBIDO ===")
        print("Dados:", data)

        nome = data.get("nome")
        email = data.get("email")

        print("Nome:", nome)
        print("Email:", email)

        link, order_nsu = criar_pagamento(nome, email)

        print("Link gerado:", link)
        print("Order NSU:", order_nsu)

        salvar_pedido(order_nsu, {
            "nome": nome,
            "email": email
        })

        print("📧 Chamando envio de email...")

        enviar_email_pagamento(nome, email, link)

        print("✅ Fim do webhook\n")

        return "OK", 200

    except Exception as e:
        print("❌ ERRO NO WEBHOOK:", e)
        return "Erro", 500

# ===============================
# CRIA PAGAMENTO
# ===============================
def criar_pagamento(nome, email):

    try:
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

        print("🔗 Criando pagamento na InfinitePay...")

        response = requests.post(url, json=payload)

        print("Status API:", response.status_code)
        print("Resposta API:", response.text)

        data = response.json()

        link = data.get("url")

        return link, order_nsu

    except Exception as e:
        print("❌ Erro ao criar pagamento:", e)
        return None, None

# ===============================
# WEBHOOK PAGAMENTO
# ===============================
@app.route("/pagamento", methods=["POST"])
def pagamento():

    try:
        data = request.get_json()

        print("\n💰 Pagamento recebido:", data)

        order_nsu = data.get("order_nsu")

        pedido = buscar_pedido(order_nsu)

        if pedido:
            print("✅ Pedido encontrado:", pedido)

            enviar_email_pdf(pedido["nome"], pedido["email"])
        else:
            print("❌ Pedido não encontrado!")

        return {"success": True}, 200

    except Exception as e:
        print("❌ ERRO NO PAGAMENTO:", e)
        return {"success": False}, 500

# ===============================
# EMAIL PAGAMENTO
# ===============================
def enviar_email_pagamento(nome, email, link):

    print("\n=== 📧 INICIANDO ENVIO EMAIL PAGAMENTO ===")

    try:
        msg = MIMEText(f"""
Olá {nome},

Para continuar:
{link}

Se precisar, pode me responder aqui.

Lucas
""")

        msg["Subject"] = "Sua solicitação"
        msg["From"] = EMAIL_REMETENTE
        msg["To"] = email

        print("🔌 Conectando ao Gmail...")

        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.set_debuglevel(1)

        servidor.starttls()

        print("🔐 Fazendo login...")
        servidor.login(EMAIL_REMETENTE, SENHA_EMAIL)

        print("📤 Enviando email...")
        servidor.send_message(msg)

        servidor.quit()

        print("✅ EMAIL ENVIADO COM SUCESSO\n")

    except Exception as e:
        print("❌ ERRO AO ENVIAR EMAIL:", e)

# ===============================
# EMAIL PDF
# ===============================
def enviar_email_pdf(nome, email):

    print("\n=== 📧 INICIANDO ENVIO PDF ===")

    try:
        msg = MIMEText(f"""
Olá {nome},

Pagamento confirmado.

Segue o material:
https://lncimg.lance.com.br/cdn-cgi/image/width=950,quality=75,fit=pad,format=webp/uploads/2024/11/AGIF24082921530730-scaled-aspect-ratio-512-320.jpg
""")

        msg["Subject"] = "Seu material"
        msg["From"] = EMAIL_REMETENTE
        msg["To"] = email

        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(EMAIL_REMETENTE, SENHA_EMAIL)

        servidor.send_message(msg)
        servidor.quit()

        print("✅ EMAIL PDF ENVIADO\n")

    except Exception as e:
        print("❌ ERRO AO ENVIAR PDF:", e)

# ===============================
# START
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
