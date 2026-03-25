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
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db import DBHandler, Ficha

load_dotenv()
LOGIN    = os.getenv("SOC_USERNAME")
PASSWORD = os.getenv("SOC_PASSWORD")
ID_EMP   = os.getenv("SOC_EMPSOC_KEY")

navegador = webdriver.Chrome()
navegador.maximize_window()
navegador.get("https://sistema.soc.com.br/WebSoc/")

wait = WebDriverWait(navegador, 10)

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

# ── Coleta todos os itens das listas ─────────────────────────────────────────
empresa              = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[1]')))
tipo_exame           = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[8]')))
todas_nomes          = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[3]')))
funcao               = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[4]')))
turno                = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[5]')))
nascimento           = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[6]')))
admissao             = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[7]')))
data_ficha           = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[9]')))
prestador_de_servico = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[10]')))

ignorar = {"Funcionário", "Mudança de Riscos Ocupacionais", "Monitoração Pontual", "Consulta"}

# ── Barra de coleta ───────────────────────────────────────────────────────────
funcionarios   = []
total_linhas   = len(todas_nomes)
ultima_empresa  = ""
ultimo_prestador = ""

print("Coletando dados do relatório...")
for i, (nome, exame, data, emp, func, tur, nasc, adm, prest) in enumerate(zip(
    todas_nomes, tipo_exame, data_ficha, empresa, funcao, turno, nascimento, admissao, prestador_de_servico
), start=1):
    nome_txt  = nome.text.strip()
    emp_txt   = emp.text.strip()  or ultima_empresa
    prest_txt = prest.text.strip() or ultimo_prestador

    if nome_txt and nome_txt not in ignorar:
        ultima_empresa   = emp_txt
        ultimo_prestador = prest_txt
        funcionarios.append({
            "nome":                 nome_txt,
            "exame":                exame.text.strip(),
            "data":                 data.text.strip(),
            "empresa":              emp_txt,
            "funcao":               func.text.strip(),
            "turno":                tur.text.strip(),
            "nascimento":           nasc.text.strip(),
            "admissao":             adm.text.strip(),
            "prestador_de_servico": prest_txt,
        })

    pct    = (i / total_linhas) * 100
    blocos = int(pct // 5)
    barra  = f"[{'█' * blocos}{'░' * (20 - blocos)}] {pct:5.1f}% — {i}/{total_linhas} linhas"
    print(f"\r{barra}", end="", flush=True)

print(f"\nColetados: {len(funcionarios)} funcionários")

# ── Remove duplicatas por nome ────────────────────────────────────────────────
# vistos = set()

funcionarios_unicos = {}
def parse_data(txt):
    try:
        return datetime.strptime(txt.strip(), "%d/%m/%Y")
    except ValueError:
        return datetime.min  # data inválida vai para o fundo

for f in funcionarios:
    nome       = f["nome"]
    data_ficha = parse_data(f["data"])

    if nome not in funcionarios_unicos:
        funcionarios_unicos[nome] = {"ficha": f, "data": data_ficha}
    else:
        if data_ficha > funcionarios_unicos[nome]["data"]:
            funcionarios_unicos[nome] = {"ficha": f, "data": data_ficha}

# ← extrai só o dicionário original, sem o datetime auxiliar
funcionarios_unicos = [v["ficha"] for v in funcionarios_unicos.values()]
funcionarios_unicos.sort(key=lambda f: f["nome"])

print(f"Únicos: {len(funcionarios_unicos)} funcionários\n")

# ── Fecha a janela do relatório e volta para a principal ──────────────────────
navegador.close()
navegador.switch_to.window(navegador.window_handles[0])
navegador.quit()

# ── Monta lista de Ficha() ────────────────────────────────────────────────────
lista_fichas = [
    Ficha(
        Empresa          = f["empresa"],
        Exames           = f["exame"],
        Funcionario      = f["nome"],
        Funcao           = f["funcao"],
        Turno            = f["turno"],
        Nascimento       = f["nascimento"],
        Admissao         = f["admissao"],
        Tip_exame        = f["exame"],
        Dt_ficha         = f["data"],
        Prest_de_servico = f["prestador_de_servico"],
    )
    for f in funcionarios_unicos
]

# ── Insere no banco com barra de progresso ────────────────────────────────────
db = DBHandler(
    host     = os.getenv("DB_HOST"),
    database = os.getenv("DB_DATABASE"),
    user     = os.getenv("DB_USER"),
    password = os.getenv("DB_PASSWORD"),
)

total_fichas = len(lista_fichas)
inseridos, erros = [], []

print("Inserindo no banco...")
with db:
    for i, ficha in enumerate(lista_fichas, start=1):
        try:
            novo_id = db.inserir(ficha)
            inseridos.append({"funcionario": ficha.Funcionario, "id": novo_id})
        except Exception as e:
            erros.append({"funcionario": ficha.Funcionario, "erro": str(e)})

        pct    = (i / total_fichas) * 100
        blocos = int(pct // 5)
        barra  = f"[{'█' * blocos}{'░' * (20 - blocos)}] {pct:5.1f}% — {i}/{total_fichas} fichas"
        print(f"\r{barra}", end="", flush=True)

print(f"\n\nInseridos: {len(inseridos)} | Ignorados/Erros: {len(erros)}")
if erros:
    print("Erros:")
    for e in erros:
        print(f"  - {e['funcionario']}: {e['erro']}")

print("\nRaspagem concluída. Execute verificacao_270.py para conferir o SOCGED.")