from flask import Flask, request
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():

    data = request.json

    nome = data.get("nome")
    email = data.get("email")

    print("Dados recebidos:", data)

    enviar_email(nome, email)

    return "ok"


def enviar_email(nome, email):

    link_pagamento = "https://invoice.infinitepay.io/feijonut/7NgEpgMrIJ"

    mensagem = f"""
Olá {nome}!

Seu plano alimentar personalizado está quase pronto.

Para liberar seu acesso basta realizar o pagamento abaixo:

{link_pagamento}

Assim que confirmado você receberá o protocolo completo.

Abraços!
"""

    msg = MIMEText(mensagem)
    msg['Subject'] = "Liberação do protocolo"
    msg['From'] = "lucasfeijorodrigues@gmail.com"
    msg['To'] = email

    servidor = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    servidor.login("lucasfeijorodrigues@gmail.com", "uxtn eqhe qxcc cgpu")
    servidor.send_message(msg)
    servidor.quit()


app.run(host="0.0.0.0", port=10000)