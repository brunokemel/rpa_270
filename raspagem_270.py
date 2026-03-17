import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
import time
from selenium.common.exceptions import NoSuchElementException

load_dotenv()
LOGIN = os.getenv("SOC_USERNAME")
PASSWORD = os.getenv("SOC_PASSWORD")
ID_EMP = os.getenv("SOC_EMPSOC_KEY")
SOC_CODE_311 = os.getenv("SOC_CODE_311")

navegador = webdriver.Chrome()
navegador.maximize_window()
navegador.get("https://sistema.soc.com.br/WebSoc/")

wait = WebDriverWait(navegador, 5)

# wai.until(EC.presence_of_element_located((By.ID, "usu"))).send_keys(LOGIN)

# Clica no campo de login para ativar o teclado virtual
container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#login > div.pteclado.holder-id > div.input-holder")))
navegador.execute_script("arguments[0].click();", container)

wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="usu"]'))).send_keys(LOGIN)
wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="senha"]'))).send_keys(PASSWORD)

# entra com JS para evitar o bloqueio do campo de empresa
campo_emp = navegador.find_element(By.XPATH, '//*[@id="empsoc"]')
navegador.execute_script("arguments[0].removeAttribute('onfocus');", campo_emp)
navegador.execute_script("arguments[0].value = arguments[1];", campo_emp, ID_EMP)

wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bt_entrar"]'))).click()

breakpoint()

wait = WebDriverWait(navegador, 10)

breakpoint() # Colocar teste joao moura

wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#cod_programa')))
navegador.execute_script("""
    var campo = document.querySelector('#cod_programa');
    campo.value = arguments[0];
""", "311")


botao = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="btn_programa"]')))
time.sleep(0.5)
botao.click()

wait = WebDriverWait(navegador, 10)

iframes = navegador.find_elements(By.TAG_NAME, "iframe")
navegador.switch_to.default_content()
navegador.switch_to.frame(iframes[1])

wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="icone"]/a/img'))).click()

wait.until(lambda d: len(d.window_handles) > 1)

abas = navegador.window_handles

navegador.switch_to.window(abas[1])

navegador.switch_to.window(abas[0])

wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#cod_programa')))
navegador.execute_script("""
    var campo = document.querySelector('#cod_programa');
    campo.value = arguments[0];
""", "229")

botao = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="btn_programa"]')))
time.sleep(0.5)
botao.click()

iframes = navegador.find_elements(By.TAG_NAME, "iframe")
navegador.switch_to.default_content()
navegador.switch_to.frame(iframes[1])

wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="socContent"]/form[1]/fieldset/p[1]/input'))).send_keys("ANGELA SOUZA DA SILVA")

todos = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="socContent"]/form[1]/fieldset/p[2]/a')))
time.sleep(0.5)
todos.click()

wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="socContent"]/form[1]/fieldset/p[1]/a/img'))).click()
wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="socContent"]/form[1]/table/tbody/tr[2]/td[1]/a'))).click()


wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="tabelaFichas"]/tbody/tr[2]/td[1]/a'))).click()

funcionario_sem_socged = []
while True:
    try:
        botao = navegador.find_element(By.XPATH, '//*[@id="botoes"]/table/tbody/tr/td[6]/a/img')
        botao.click()

    except NoSuchElementException:
        try:
            funcionario = navegador.find_element(
                By.XPATH,
                '//*[@id="cad009"]/age_substituir_cabec_log/table[1]/tbody/tr[2]/td/table/tbody/tr[1]/td[2]'
            ).text
            funcionario_sem_socged.append(funcionario)
        except NoSuchElementException:
            funcionario_sem_socged.append("Nome não encontrado")

    time.sleep(5)

# //*[@id="socContent"]/form[1]/fieldset/p[1]/input

# //*[@id="socContent"]/form[1]/fieldset/p[1]/a/img

# //*[@id="socContent"]/form[1]/table/tbody/tr[2]/td[1]/a

#  ANGELA SOUZA DA SILVA = Check
#  ARIMAR PEREIRA DE ANDRADE => Fail

# validar SOCGED e Data com condicional para enviar email ou não
# Avaliar melhor forma de pegar os dados e enviar por email

