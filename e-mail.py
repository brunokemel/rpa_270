import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import xml.etree.ElementTree as ET

load_dotenv()

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_DESTINO = os.getenv('EMAIL_DESTINO')

def enviar_email_solicitacao(destinatario, assunto, mensagem):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(mensagem, 'plain'))

        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, destinatario, msg.as_string())
        server.quit()
        print("Email enviado com sucesso.")
    except Exception as e:
        print(f"Erro ao enviar email: {e}")

arvore = ET.parse("sem_socged.xml")
raiz = arvore.getroot()

sem_socged = [filho.text for filho in raiz.findall("funcionario")]

lista_nomes = "\n".join(sem_socged)

enviar_email_solicitacao(
    destinatario=EMAIL_DESTINO,
    assunto="Funcionários sem SOCGED",
    mensagem=f"Total de funcionários sem SOCGED: {len(sem_socged)}\n\n{lista_nomes}"
)