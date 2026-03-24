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

# ── Busca fichas pendentes no banco ───────────────────────────────────────────
with db:
    fichas_pendentes = db.buscar_nao_verificados()

if not fichas_pendentes:
    print("Nenhuma ficha pendente de verificação.")
    exit()

print(f"{len(fichas_pendentes)} ficha(s) pendente(s)\n")

# ── Abre navegador e faz login ────────────────────────────────────────────────
navegador = webdriver.Chrome()
navegador.maximize_window()
navegador.get("https://sistema.soc.com.br/WebSoc/")

wait = WebDriverWait(navegador, 5)

container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#login > div.pteclado.holder-id > div.input-holder")))
navegador.execute_script("arguments[0].click();", container)

wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="usu"]'))).send_keys(LOGIN)
wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="senha"]'))).send_keys(PASSWORD)

campo_emp = navegador.find_element(By.XPATH, '//*[@id="empsoc"]')
navegador.execute_script("arguments[0].removeAttribute('onfocus');", campo_emp)
navegador.execute_script("arguments[0].value = arguments[1];", campo_emp, ID_EMP)

wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bt_entrar"]'))).click()

breakpoint()

wait = WebDriverWait(navegador, 10)

# ── Processa cada ficha do banco no programa 229 ──────────────────────────────
sem_socged = []

for ficha in fichas_pendentes:     # PK do banco
    nome     = ficha["Funcionario"]
    exame    = ficha["Tip_exame"].strip()
    data     = ficha["Dt_ficha"].strip()

    print(f"\nVerificando: {nome} | {exame} | {data}")

    try:
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
        indice           = 2    # tr[2] = primeiro funcionário na tabela

        while not clicou:
            try:
                # ── Pesquisa o nome ───────────────────────────────────────────
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

                # ── Verifica se o resultado no índice existe ──────────────────
                # O texto desse link é o Sequencial_ficha — salva antes de clicar
                try:
                    link_resultado = wait.until(EC.presence_of_element_located((
                        By.XPATH, f'//*[@id="socContent"]/form[1]/table/tbody/tr[{indice}]/td[1]/a'
                    )))
                except TimeoutException:
                    print(f"  ⚠ Sem mais resultados para {nome} (parou em tr[{indice}])")
                    break

                navegador.execute_script("arguments[0].click();", link_resultado)

                # ── Aguarda tabelaFichas carregar ─────────────────────────────
                try:
                    wait.until(EC.presence_of_element_located((
                        By.XPATH, "//*[@id='tabelaFichas']/tbody/tr"
                    )))
                except TimeoutException:
                    print(f"  ⚠ tabelaFichas não carregou em tr[{indice}], avançando...")
                    sequencial_ficha = None
                    indice += 1
                    navegador.back()
                    wait.until(EC.presence_of_element_located((
                        By.XPATH, '//*[@id="socContent"]/form[1]/fieldset/p[1]/input'
                    )))
                    continue

                # ── Percorre linhas da tabelaFichas e bate data + exame ───────
                linhas = navegador.find_elements(By.XPATH, "//*[@id='tabelaFichas']/tbody/tr")
                for linha in linhas:
                    try:
                        data_td  = linha.find_element(By.XPATH, "./td[1]").text.strip()
                        exame_td = linha.find_element(By.XPATH, "./td[2]").text.strip()

                        if data_td == data and exame_td == exame:
                            link_ficha = linha.find_element(By.XPATH, "./td[1]/a")
                            navegador.execute_script("arguments[0].click();", link_ficha)

                            # ── Coleta Sequencial_ficha dentro da ficha aberta ─
                            try:
                                seq_el = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="cad009"]/age_substituir_cabec_log//table/tbody/tr[4]/td/table/tbody/tr[2]/td[4]')))
                                sequencial_ficha = int(seq_el.text.strip())
                                print(f"  ✔ Dados batem! Sequencial_ficha: {sequencial_ficha}")
                            except Exception as e:
                                print(f"  ⚠ Não conseguiu ler Sequencial_ficha: {e}")
                                sequencial_ficha = 0

                            clicou = True
                            break
                    except Exception:
                        continue

                if clicou:
                    break

                # Dados não bateram — volta e tenta o próximo índice
                print(f"  Dados não bateram em tr[{indice}], tentando tr[{indice + 1}]...")
                sequencial_ficha = None
                indice += 1

                # Volta para a lista de resultados sem recarregar o programa 229
                navegador.back()
                wait.until(EC.presence_of_element_located((
                    By.XPATH, '//*[@id="socContent"]/form[1]/fieldset/p[1]/input'
                )))

            except Exception as e:
                print(f"  Erro ao processar tr[{indice}]: {e}")
                break
        # ── FIM do while ──────────────────────────────────────────────────────

        # ── Ficha não encontrada ──────────────────────────────────────────────
        if not clicou:
            print(f"  ⚠ Nenhuma ficha encontrada: {nome} | {exame} | {data}")
            sem_socged.append({"nome": nome, "exame": exame, "data": data})
            with db:
                db.atualizar_verificacao(nome, data, exame, 0, socged=0)
            continue

        # ── Fecha overlay de aniversário se aparecer ──────────────────────────
        try:
            element = wait.until(EC.presence_of_element_located((
                By.XPATH, '//*[@id="idaniversario"]/div[1]/a[1]'
            )))
            navegador.execute_script("arguments[0].click();", element)
            time.sleep(0.5)
            print("  Overlay fechado.")
        except Exception:
            pass

        # ── Verifica botão SOCGED e atualiza banco ────────────────────────────
        try:
            navegador.find_element(By.XPATH, '//*[@id="botoes"]/table/tbody/tr/td[6]/a/img')
            print(f"  ✔ possui SOCGED")
            with db:
                db.atualizar_verificacao(nome, data, exame, sequencial_ficha or 0, socged=1)

        except NoSuchElementException:
            print(f"  ✘ SEM SOCGED → {nome} | {exame} | {data}")
            sem_socged.append({"nome": nome, "exame": exame, "data": data})
            with db:
                db.atualizar_verificacao(nome, data, exame, sequencial_ficha or 0, socged=0)

    except TimeoutException:
        print(f"  ⚠ Timeout: {nome}")
        sem_socged.append({"nome": nome, "exame": exame, "data": data})
        with db:
            db.atualizar_verificacao(nome, data, exame, 0, socged=0)

navegador.quit()

# ── Salva XML para o mail.py ──────────────────────────────────────────────────
raiz = ET.Element("funcionarios_sem_socged")
raiz.set("total", str(len(sem_socged)))

for f in sem_socged:
    filho = ET.SubElement(raiz, "funcionario")
    filho.set("exame", f.get("exame", ""))
    filho.set("data",  f.get("data", ""))
    filho.text = f.get("nome", "")

arvore = ET.ElementTree(raiz)
ET.indent(arvore, space="  ")
arvore.write("sem_socged.xml", encoding="utf-8", xml_declaration=True)

print(f"\n{'─'*50}")
print(f"Total sem SOCGED: {len(sem_socged)}")
print("Arquivo 'sem_socged.xml' salvo — pronto para o mail.py")
