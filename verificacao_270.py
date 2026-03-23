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

with db:
    fichas_pendentes = db.buscar_nao_verificados()


if not fichas_pendentes:
    print("Nenhuma ficha pendente de verificação.")
    exit()

print(f"{len(fichas_pendentes)} ficha(s) pendente(s) de verificação.\n")

# abre o navegador
navegador = webdriver.Chrome()
navegador.maximize_window()
navegador.get("https://sistema.soc.com.br/WebSoc/")

wait = WebDriverWait(navegador, 5)

# login

container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#login > div.pteclado.holder-id > div.input-holder")))
navegador.execute_script("arguments[0].click();", container)

wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="usu"]'))).send_keys(LOGIN)
wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="senha"]'))).send_keys(PASSWORD)

campo_emp = navegador.find_element(By.XPATH, '//*[@id="empsoc"]')
navegador.execute_script("arguments[0].removeAttribute('onfocus');", campo_emp)
navegador.execute_script("arguments[0].value = arguments[1];", campo_emp, ID_EMP)

wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bt_entrar"]'))).click()

breakpoint()

wait = WebDriverWait(navegador, 5)

# verificar na 229
sem_socged = []

for ficha in fichas_pendentes:
    id_banco = ficha["Sequencial_fic"]   # PK do banco
    nome     = ficha["Funcionario"]
    exame    = ficha["Exames"]
    data     = ficha["Dt_ficha"]

    try:
        print(f"\nVerificando: {nome} | Exame: {exame} | Data: {data}")

        navegador.switch_to.default_content()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#cod_programa')))
        navegador.execute_script("document.querySelector('#cod_programa').value = '229';")

        botao = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="btn_programa"]')))
        time.sleep(0.5)
        botao.click()

        iframes = navegador.find_elements(By.TAG_NAME, "iframe")
        navegador.switch_to.default_content()
        navegador.switch_to.frame(iframes[1])

        clicou           = False
        sequencial_ficha = None
        indice           = 2   # tr[2] = primeiro resultado na tabela

        while not clicou:
            try:
                # Pesquisa o funcionário
                campo_nome = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="socContent"]/form[1]/fieldset/p[1]/input')
                ))
                campo_nome.clear()
                campo_nome.send_keys(nome)

                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="socContent"]/form[1]/fieldset/p[2]/a')
                )).click()

                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="socContent"]/form[1]/fieldset/p[1]/a/img')
                )).click()

                # Verifica se o resultado no índice atual existe
                try:
                    link_resultado = wait.until(EC.presence_of_element_located(
                        (By.XPATH, f'//*[@id="socContent"]/form[1]/table/tbody/tr[{indice}]/td[1]/a')
                    ))
                except TimeoutException:
                    print(f"  ⚠ Sem mais resultados para {nome} (parou em tr[{indice}])")
                    break

                # Clica no resultado e aguarda tabelaFichas
                navegador.execute_script("arguments[0].click();", link_resultado)

                try:
                    wait.until(EC.presence_of_element_located(
                        (By.XPATH, "//*[@id='tabelaFichas']/tbody/tr")
                    ))
                except TimeoutException:
                    print(f"  ⚠ tabelaFichas não carregou em tr[{indice}], avançando...")
                    indice += 1
                    navegador.switch_to.default_content()
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#cod_programa')))
                    navegador.execute_script("document.querySelector('#cod_programa').value = '229';")
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="btn_programa"]'))).click()
                    iframes = navegador.find_elements(By.TAG_NAME, "iframe")
                    navegador.switch_to.default_content()
                    navegador.switch_to.frame(iframes[1])
                    continue

                # Bate data + exame para achar a ficha certa
                linhas = navegador.find_elements(By.XPATH, "//*[@id='tabelaFichas']/tbody/tr")
                for linha in linhas:
                    try:
                        data_td  = linha.find_element(By.XPATH, "./td[1]").text.strip()
                        exame_td = linha.find_element(By.XPATH, "./td[2]").text.strip()

                        if data_td == data and exame_td == exame:
                            link_ficha = linha.find_element(By.XPATH, "./td[1]/a")

                            # ── Coleta o Sequencial_ficha do texto do link ────
                            sequencial_ficha = int(link_ficha.text.strip())
                            print(f"  Sequencial_ficha: {sequencial_ficha}")

                            navegador.execute_script("arguments[0].click();", link_ficha)
                            clicou = True
                            print(f"  ✔ Ficha encontrada: {nome} | {exame} | {data} | tr[{indice}]")
                            break
                    except Exception:
                        continue

                if clicou:
                    break

                print(f"  Não bateu em tr[{indice}], tentando tr[{indice + 1}]...")
                indice += 1

                navegador.switch_to.default_content()
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#cod_programa')))
                navegador.execute_script("document.querySelector('#cod_programa').value = '229';")
                wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="btn_programa"]'))).click()
                iframes = navegador.find_elements(By.TAG_NAME, "iframe")
                navegador.switch_to.default_content()
                navegador.switch_to.frame(iframes[1])

            except Exception as e:
                print(f"  Erro em tr[{indice}]: {e}")
                break

        # ── Ficha não encontrada no 229 ───────────────────────────────────────
        if not clicou:
            print(f"  ⚠ Ficha não encontrada: {nome} | {exame} | {data}")
            sem_socged.append(ficha)
            with db:
                db.atualizar_verificacao(id_banco, sequencial_ficha or 0, socged=0)
            continue

        # Fecha overlay de aniversário se aparecer
        try:
            element = wait.until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="idaniversario"]/div[1]/a[1]')
            ))
            navegador.execute_script("arguments[0].click();", element)
            time.sleep(0.5)
        except Exception:
            pass

        # ── Verifica se o botão SOCGED existe e atualiza o banco ─────────────
        try:
            navegador.find_element(By.XPATH, '//*[@id="botoes"]/table/tbody/tr/td[6]/a/img')
            print(f"  ✔ possui SOCGED")
            with db:
                db.atualizar_verificacao(id_banco, sequencial_ficha, socged=1)

        except NoSuchElementException:
            print(f"  ✘ SEM SOCGED → {nome} | {exame} | {data}")
            sem_socged.append(ficha)
            with db:
                db.atualizar_verificacao(id_banco, sequencial_ficha, socged=0)

    except TimeoutException:
        print(f"  ⚠ Timeout: {nome}")
        sem_socged.append(ficha)
        with db:
            db.atualizar_verificacao(id_banco, sequencial_ficha or 0, socged=0)

navegador.quit()

# ── Salva XML dos sem SOCGED (usado pelo mail.py) ─────────────────────────────
raiz = ET.Element("funcionarios_sem_socged")
raiz.set("total", str(len(sem_socged)))

for f in sem_socged:
    filho = ET.SubElement(raiz, "funcionario")
    filho.set("exame", f.get("Exames", ""))
    filho.set("data",  f.get("Dt_ficha", ""))
    filho.text = f.get("Funcionario", "")

arvore = ET.ElementTree(raiz)
ET.indent(arvore, space="  ")
arvore.write("sem_socged.xml", encoding="utf-8", xml_declaration=True)

print(f"\n{'─'*50}")
print(f"Total sem SOCGED: {len(sem_socged)}")
print(f"Arquivo 'sem_socged.xml' salvo — pronto para o mail.py")
