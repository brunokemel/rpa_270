import os
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()

def rodar(script: str):
    print(f"\n{'─'*50}")
    print(f"▶ Executando {script}...")
    print(f"{'─'*50}")
    resultado = subprocess.run([sys.executable, script], check=True)
    return resultado.returncode

if __name__ == "__main__":
    try:
        rodar("raspagem_270.py")   # 1️⃣ coleta do SOC e insere no banco
        rodar("verificacao_270.py") # 2️⃣ verifica SOCGED no programa 229
        rodar("mail.py")            # 3️⃣ envia email com os sem SOCGED
        print("\n✅ Pipeline concluído com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro ao executar pipeline: {e}")
        sys.exit(1)