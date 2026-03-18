import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def enviar_email(nome, email):
    message = Mail(
        from_email='SEUEMAIL@gmail.com',
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
