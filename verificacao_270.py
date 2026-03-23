import os
import sys
import time
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db import DBHandler


# CONFIG
load_dotenv()

LOGIN    = os.getenv("SOC_USERNAME")
PASSWORD = os.getenv("SOC_PASSWORD")
ID_EMP   = os.getenv("SOC_EMPSOC_KEY")

db = DBHandler(
    host     = os.getenv("DB_HOST"),
    database = os.getenv("DB_DATABASE"),
    user     = os.getenv("DB_USER"),
    password = os.getenv("DB_PASSWORD"),
)


# FUNÇÃO PRINCIPAL 229
def verificar_ficha_229(navegador, wait, ficha):
    nome  = ficha["Funcionario"]
    exame = ficha["Tip_exame"].strip().lower()
    data  = ficha["Dt_ficha"].strip()

    print(f"\n🔎 Verificando: {nome} | {exame} | {data}")

    for tentativa in range(3):
        try:
            navegador.switch_to.default_content()

            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#cod_programa')))
            navegador.execute_script("document.querySelector('#cod_programa').value = '229';")

            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="btn_programa"]'))).click()

            iframes = navegador.find_elements(By.TAG_NAME, "iframe")
            navegador.switch_to.frame(iframes[1])

            indice = 2

            while True:
                try:
                    campo_nome = wait.until(EC.element_to_be_clickable((
                        By.XPATH, '//*[@id="socContent"]/form[1]/fieldset/p[1]/input'
                    )))
                    campo_nome.clear()
                    campo_nome.send_keys(nome)

                    wait.until(EC.element_to_be_clickable((
                        By.XPATH, '//*[@id="socContent"]/form[1]/fieldset/p[2]/a'
                    ))).click()

                    wait.until(EC.element_to_be_clickable((
                        By.XPATH, '//*[@id="socContent"]/form[1]/fieldset/p[1]/a/img'
                    ))).click()

                    try:
                        link = wait.until(EC.presence_of_element_located((
                            By.XPATH, f'//*[@id="socContent"]/form[1]/table/tbody/tr[{indice}]/td[1]/a'
                        )))
                    except TimeoutException:
                        print(f"⚠ Sem resultados: {nome}")
                        return None, 0

                    navegador.execute_script("arguments[0].click();", link)

                    wait.until(EC.presence_of_element_located((
                        By.XPATH, "//*[@id='tabelaFichas']/tbody/tr"
                    )))

                    linhas = navegador.find_elements(By.XPATH, "//*[@id='tabelaFichas']/tbody/tr")

                    for linha in linhas:
                        try:
                            data_td  = linha.find_element(By.XPATH, "./td[1]").text.strip()
                            exame_td = linha.find_element(By.XPATH, "./td[2]").text.strip().lower()

                            if data_td == data and exame_td == exame:

                                link_ficha = linha.find_element(By.XPATH, "./td[1]/a")

                                sequencial = int(link_ficha.text.strip())

                                navegador.execute_script("arguments[0].click();", link_ficha)

                                # verificar SOCGED
                                try:
                                    navegador.find_element(By.XPATH, '//*[@id="botoes"]/table/tbody/tr/td[6]/a/img')
                                    socged = 1
                                except NoSuchElementException:
                                    socged = 0

                                return sequencial, socged

                        except Exception:
                            continue

                    indice += 1
                    navegador.switch_to.default_content()

                except Exception:
                    break

        except Exception:
            print(f"🔁 Retry {tentativa+1}")
            time.sleep(2)

    return None, 0



# BUSCA NO BANCO
with db:
    fichas_pendentes = db.buscar_nao_verificados()

if not fichas_pendentes:
    print("Nenhuma ficha pendente.")
    exit()

print(f"{len(fichas_pendentes)} ficha(s) pendente(s)\n")


# SELENIUM
navegador = webdriver.Chrome()
navegador.maximize_window()
navegador.get("https://sistema.soc.com.br/WebSoc/")

wait = WebDriverWait(navegador, 10)

# LOGIN
container = wait.until(EC.presence_of_element_located((
    By.CSS_SELECTOR, "#login > div.pteclado.holder-id > div.input-holder"
)))
navegador.execute_script("arguments[0].click();", container)

wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="usu"]'))).send_keys(LOGIN)
wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="senha"]'))).send_keys(PASSWORD)

campo_emp = navegador.find_element(By.XPATH, '//*[@id="empsoc"]')
navegador.execute_script("arguments[0].removeAttribute('onfocus');", campo_emp)
navegador.execute_script("arguments[0].value = arguments[1];", campo_emp, ID_EMP)

wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bt_entrar"]'))).click()


# PROCESSAMENTO
sem_socged = []

for ficha in fichas_pendentes:
    id_banco = ficha["id"]
    nome     = ficha["Funcionario"]

    try:
        sequencial, socged = verificar_ficha_229(navegador, wait, ficha)

        print(f"✔ {nome} → seq={sequencial} | socged={socged}")

        db.atualizar_verificacao(
            id_banco=id_banco,
            sequencial_ficha=sequencial if sequencial else 0,
            socged=socged
        )

        if socged == 0:
            sem_socged.append(ficha)

    except Exception as e:
        print(f"❌ Erro: {nome} | {e}")

        db.atualizar_verificacao(
            id_banco=id_banco,
            sequencial_ficha=0,
            socged=0
        )

        sem_socged.append(ficha)

navegador.quit()

# XML
raiz = ET.Element("funcionarios_sem_socged")
raiz.set("total", str(len(sem_socged)))

for f in sem_socged:
    filho = ET.SubElement(raiz, "funcionario")
    filho.set("exame", f.get("Tip_exame", ""))
    filho.set("data",  f.get("Dt_ficha", ""))
    filho.text = f.get("Funcionario", "")

arvore = ET.ElementTree(raiz)
ET.indent(arvore, space="  ")
arvore.write("sem_socged.xml", encoding="utf-8", xml_declaration=True)

print(f"\n{'─'*50}")
print(f"Total sem SOCGED: {len(sem_socged)}")
print("Arquivo 'sem_socged.xml' salvo!")