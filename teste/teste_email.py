import sys
sys.path.insert(0, r"C:\Users\Kemel\Desktop\TRABALHO\rpa_envio_270")

from mail import enviar_email, gerar_html, EMAIL_DESTINO
import xml.etree.ElementTree as ET

arvore       = ET.parse(r"C:\Users\Kemel\Desktop\TRABALHO\rpa_envio_270\sem_socged.xml")
raiz         = arvore.getroot()
funcionarios = [f.text.strip() for f in raiz.findall("funcionario") if f.text]
total        = len(funcionarios)

enviar_email(
    destinatario=EMAIL_DESTINO,
    assunto=f"⚠️ {total} funcionário(s) sem SOCGED",
    html_conteudo=gerar_html(funcionarios)
)