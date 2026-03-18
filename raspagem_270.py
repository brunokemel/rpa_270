import os
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.common.exceptions import NoSuchElementException, TimeoutException

load_dotenv()
LOGIN = os.getenv("SOC_USERNAME")
PASSWORD = os.getenv("SOC_PASSWORD")
ID_EMP = os.getenv("SOC_EMPSOC_KEY")

navegador = webdriver.Chrome()
navegador.maximize_window()
navegador.get("https://sistema.soc.com.br/WebSoc/")

wait = WebDriverWait(navegador, 5)

# ── Login ─────────────────────────────────────────────────────────────────────
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

breakpoint()

# ── Abre programa 311 ─────────────────────────────────────────────────────────
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#cod_programa')))
navegador.execute_script("document.querySelector('#cod_programa').value = '311';")

botao = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="btn_programa"]')))
time.sleep(0.5)
botao.click()

wait = WebDriverWait(navegador, 10)

iframes = navegador.find_elements(By.TAG_NAME, "iframe")
navegador.switch_to.default_content()
navegador.switch_to.frame(iframes[1])

wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="icone"]/a/img'))).click()

# ── Troca para a nova janela com a lista ──────────────────────────────────────
wait.until(lambda d: len(d.window_handles) > 1)
navegador.switch_to.window(navegador.window_handles[-1])

time.sleep(2)

# ── Coleta nomes a partir de tr[3] ignorando cabeçalhos repetidos ─────────────
funcionarios = []
linha = 3

while True:
    try:
        nome = navegador.find_element(
            By.XPATH, f'//*[@id="rel005"]/table/tbody/tr[{linha}]/td[3]'
        ).text.strip()

        if nome and nome != "Funcionário":
            funcionarios.append(nome)
            print(f"Coletado tr[{linha}]: {nome}")

        linha += 1

    except NoSuchElementException:
        break

# Remove duplicatas mantendo a ordem
funcionarios = list(dict.fromkeys(funcionarios))
print(f"\nTotal coletado: {len(funcionarios)}")

# ── Fecha a janela do relatório e volta para a principal ──────────────────────
navegador.close()
navegador.switch_to.window(navegador.window_handles[0])

# ── Verifica cada funcionário no programa 229 ─────────────────────────────────
sem_socged = []

for nome in funcionarios:
    try:
        print(f"Verificando: {nome}")

        navegador.switch_to.default_content()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#cod_programa')))
        navegador.execute_script("document.querySelector('#cod_programa').value = '229';")

        botao = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="btn_programa"]')))
        time.sleep(0.5)
        botao.click()

        iframes = navegador.find_elements(By.TAG_NAME, "iframe")
        navegador.switch_to.default_content()
        navegador.switch_to.frame(iframes[1])

        # Pesquisa o funcionário
        campo_nome = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="socContent"]/form[1]/fieldset/p[1]/input')
        ))
        campo_nome.clear()
        campo_nome.send_keys(nome)

        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="socContent"]/form[1]/fieldset/p[2]/a')
        )).click()
        time.sleep(0.5)

        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="socContent"]/form[1]/fieldset/p[1]/a/img')
        )).click()

        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="socContent"]/form[1]/table/tbody/tr[2]/td[1]/a')
        )).click()

        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="tabelaFichas"]/tbody/tr[2]/td[1]/a')
        )).click()

        time.sleep(2)

        # ── Verifica se o botão SOCGED existe ────────────────────────────────
        try:
            navegador.find_element(By.XPATH, '//*[@id="botoes"]/table/tbody/tr/td[6]/a/img')
            print(f"  ✔ possui SOCGED")

        except NoSuchElementException:
            try:
                info = navegador.find_element(
                    By.XPATH,
                    '//*[@id="cad009"]/age_substituir_cabec_log/table[1]/tbody/tr[2]/td/table/tbody/tr[1]/td[2]'
                ).text.strip()
            except NoSuchElementException:
                info = nome

            sem_socged.append(info)
            print(f"  ✘ SEM SOCGED → {info}")

    except TimeoutException:
        print(f"  ⚠ Timeout: {nome}")
        sem_socged.append(f"ERRO_TIMEOUT - {nome}")

# ── Salva XML ─────────────────────────────────────────────────────────────────
raiz = ET.Element("funcionarios_sem_socged")
raiz.set("total", str(len(sem_socged)))

for entry in sem_socged:
    filho = ET.SubElement(raiz, "funcionario")
    filho.text = entry

arvore = ET.ElementTree(raiz)
ET.indent(arvore, space="  ")
arvore.write("sem_socged.xml", encoding="utf-8", xml_declaration=True)

print(f"\nTotal sem SOCGED: {len(sem_socged)}")
print("Arquivo 'sem_socged.xml' salvo!")