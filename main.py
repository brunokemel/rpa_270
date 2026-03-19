import os
from dotenv import load_dotenv

load_dotenv()

from raspagem_270 import executar_raspagem
from mail import enviar_email, gerar_html, EMAIL_DESTINO

def main():
    sem_socged = executar_raspagem()
    total = len(sem_socged)

    if total > 0:
        html = gerar_html(sem_socged)
        enviar_email(
            destinatario=EMAIL_DESTINO,
            assunto=f"⚠️ {total} funcionário(s) sem SOCGED",
            html_conteudo=html
        )
    else:
        print("✅ Todos os funcionários possuem SOCGED.")

if __name__ == "__main__":
    main()