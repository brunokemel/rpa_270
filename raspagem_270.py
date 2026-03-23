import os
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db import DBHandler, Ficha

load_dotenv()
LOGIN    = os.getenv("SOC_USERNAME")
PASSWORD = os.getenv("SOC_PASSWORD")
ID_EMP   = os.getenv("SOC_EMPSOC_KEY")

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

# ── Coleta todos os itens das listas (Empresa, exames, Funciona/Nome, Funcao, Turno, Nascimento, Admissao, Tipo, Dt_ficha e prestador de servico )──────────────────────────────────
empresa = navegador.find_elements(By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[1]')
tipo_exame  = navegador.find_elements(By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[8]')
todas_nomes = navegador.find_elements(By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[3]') 
funcao = navegador.find_elements(By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[4]')
turno = navegador.find_elements(By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[5]')
nascimento = navegador.find_elements(By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[6]')
admissao = navegador.find_elements(By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[7]')
data_ficha  = navegador.find_elements(By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[9]')
prestador_de_servico = navegador.find_elements(By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[10]')

ignorar = {"Funcionário", "Mudança de Riscos Ocupacionais", "Monitoração Pontual", "Consulta"}

funcionarios = []
for nome, exame, data, emp, func, tur, nasc, adm, prest in zip(
    todas_nomes, tipo_exame, data_ficha, empresa, funcao, turno, nascimento, admissao, prestador_de_servico
):
    nome_txt = nome.text.strip()
    if nome_txt and nome_txt not in ignorar:
        funcionarios.append({
            "nome":                 nome_txt,
            "exame":                exame.text.strip(),
            "data":                 data.text.strip(),
            "empresa":              emp.text.strip(),
            "funcao":               func.text.strip(),
            "turno":                tur.text.strip(),
            "nascimento":           nasc.text.strip(),
            "admissao":             adm.text.strip(),
            "prestador_de_servico": prest.text.strip(),
        })
        print(f"Coletado: {nome_txt} | Exame: {exame.text.strip()} | Data: {data.text.strip()}")

vistos = set()
funcionarios_unicos = []
for f in funcionarios:
    if f["nome"] not in vistos:
        funcionarios_unicos.append(f)
        vistos.add(f["nome"])

print(f"\nTotal coletado: {len(funcionarios_unicos)}")

# ── Fecha a janela do relatório e volta para a principal ──────────────────────
navegador.close()
navegador.switch_to.window(navegador.window_handles[0])
navegador.quit()

# ── Monta lista de Ficha() e insere no banco ──────────────────────────────────
# Sequencial_ficha = NULL (será preenchido pela verificacao_270.py)
# socged           = NULL (será preenchido pela verificacao_270.py)
lista_fichas = [
    Ficha(
        Empresa        = f["empresa"],
        Exames         = f["exame"],
        Funcionario    = f["nome"],
        Funcao         = f["funcao"],
        Turno          = f["turno"],
        Nascimento     = f["nascimento"],
        Admissao       = f["admissao"],
        Tip_exame      = f["exame"],
        Dt_ficha       = f["data"],
        Prest_de_servi = f["prestador_de_servico"],
    )
    for f in funcionarios_unicos
]

db = DBHandler(
    host     = os.getenv("DB_HOST"),
    database = os.getenv("DB_DATABASE"),
    user     = os.getenv("DB_USER"),
    password = os.getenv("DB_PASSWORD"),
)

with db:
    relatorio = db.inserir_lista(lista_fichas)

print(f"\nInseridos: {len(relatorio['inseridos'])} | Erros: {len(relatorio['erros'])}")
if relatorio["erros"]:
    print("Erros:")
    for e in relatorio["erros"]:
        print(f"  - {e['funcionario']}: {e['erro']}")

print("\nRaspagem concluída. Execute verificacao_270.py para conferir o SOCGED.")