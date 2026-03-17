import os
from dotenv import load_dotenv
from raspagem_270 import verificar_exame_soc
from email import enviar_email_solicitacao

load_dotenv()

SOC_CODE_270 = os.getenv('SOC_CODE_270')

def main():
    tem_exame = verificar_exame_soc(SOC_CODE_270)

    if not tem_exame:
        destinatario = 'responsavel@empresa.com'
        assunto = 'Solicitação de Imagem do Exame - Código 270'
        mensagem = f'Prezado,\n\nSolicitamos a imagem do exame para o código {SOC_CODE_270}.\n\nAtenciosamente,\nSistema RPA'
        enviar_email_solicitacao(destinatario, assunto, mensagem)
    else:
        print("Exame encontrado no SOC. Prosseguindo com o processamento...")

if __name__ == "__main__":
    main()
