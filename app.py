from flask import Flask, request
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)

@app.route("/")
def home():
    return "Servidor funcionando!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    nome = data.get("nome")
    email = data.get("email")

    print("Dados recebidos:", data)

    enviar_email(nome, email)

    return "OK", 200

def enviar_email(nome, email):
    message = Mail(
        from_email='lucasfeijorodrigues@gmail.com',
        to_emails=email,
        subject='Seu link de pagamento',
        html_content=f"""
        <p>Olá {nome},</p>
        <p>Clique abaixo para pagar:</p>
        <a href="https://invoice.infinitepay.io/feijonut/7NgEpgMrIJ">
        PAGAR AGORA
        </a>
        """
    )

    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print("Email enviado!", response.status_code)
    except Exception as e:
        print("Erro ao enviar email:", e)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
