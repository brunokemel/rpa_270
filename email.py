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

def enviar_email_html(destinatario, assunto, html_conteudo):
    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = EMAIL_USER
        msg['To'] = destinatario
        msg['Subject'] = assunto

        # corpo em HTML
        msg.attach(MIMEText(html_conteudo, 'html'))

        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, destinatario, msg.as_string())
        server.quit()
        print("Email enviado com sucesso.")
    except Exception as e:
        print(f"Erro ao enviar email: {e}")

# Parse do XML
arvore = ET.parse("sem_socged.xml")
raiz = arvore.getroot()

funcionarios = [filho.text for filho in raiz.findall("funcionario")]

# Montar HTML
html_tabela = """
<html>
<head>
  <style>
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
    th {{ background-color: #f4f4f4; }}
  </style>
</head>
<body>
  <h2>Funcionários sem SOCGED</h2>
  <p>Total: {total}</p>
  <table>
    <tr><th>Nome</th></tr>
    {linhas}
  </table>
</body>
</html>
""".format(
    total=len(funcionarios),
    linhas="".join(f"<tr><td>{nome}</td></tr>" for nome in funcionarios)
)

# Enviar email com HTML
enviar_email_html(
    destinatario=EMAIL_DESTINO,
    assunto="Funcionários sem SOCGED",
    html_conteudo=html_tabela
)
