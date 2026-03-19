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

# ── Coleta todos os nomes de todas as listas ──────────────────────────────────
todas_nomes = navegador.find_elements(By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[3]')
tipo_exame = navegador.find_elements(By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[8]')
data_ficha = navegador.find_elements(By.XPATH, '//*[@id="rel005"]/table/tbody/tr/td[9]')

ignorar = {"Funcionário", "Mudança de Riscos Ocupacionais", "Monitoração Pontual", "Consulta"}

funcionarios = []
for nome, exame, data in zip(todas_nomes, tipo_exame, data_ficha):
    nome_txt = nome.text.strip()
    if nome_txt and nome_txt not in ignorar:
        funcionarios.append({
            "nome": nome_txt,
            "exame": exame.text.strip(),
            "data": data.text.strip()
        })
        print(f"Coletado: {nome_txt} | Exame: {exame.text.strip()} | Data: {data.text.strip()}")

funcionarios_unicos = []
vistos = set()
for f in funcionarios:
    if f["nome"] not in vistos:
        funcionarios_unicos.append(f)
        vistos.add(f["nome"])

print(f"\nTotal coletado: {len(funcionarios_unicos)}")

# ── Fecha a janela do relatório e volta para a principal ──────────────────────
navegador.close()
navegador.switch_to.window(navegador.window_handles[0])

# ── Verifica cada funcionário no programa 229 ─────────────────────────────────
sem_socged = []
# pular_ate = "ANA PAULA DA SILVA"
# encontrado = False

for f in funcionarios:
    nome = f["nome"]
    exame = f["exame"]
    data = f["data"]

    # if not encontrado:
    #     if nome == pular_ate:
    #         encontrado = True
    #     else:
    #         print(f"Pulando: {nome}")
    #         continue

    try:
        print(f"Verificando: {nome} | Exame: {exame} | Data: {data}")

        navegador.switch_to.default_content()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#cod_programa')))
        navegador.execute_script("document.querySelector('#cod_programa').value = '229';")

        botao = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="btn_programa"]')))
        time.sleep(0.5)
        botao.click()

        iframes = navegador.find_elements(By.TAG_NAME, "iframe")
        navegador.switch_to.default_content()
        navegador.switch_to.frame(iframes[1])

        # ── Percorre todos os resultados repesquisando a cada volta ───────────
        clicou = False
        indice = 2  # começa no tr[2]

        while not clicou:
            try:
                # Repesquisa sempre antes de clicar
                campo_nome = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="socContent"]/form[1]/fieldset/p[1]/input')
                ))
                campo_nome.clear()
                campo_nome.send_keys(nome)

                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="socContent"]/form[1]/fieldset/p[2]/a')
                )).click()
                # time.sleep(0.5)

                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="socContent"]/form[1]/fieldset/p[1]/a/img')
                )).click()
                # time.sleep(0.5)

                # Verifica se o índice atual existe
                try:
                    link_resultado = navegador.find_element(
                        By.XPATH, f'//*[@id="socContent"]/form[1]/table/tbody/tr[{indice}]/td[1]/a'
                    )
                except NoSuchElementException:
                    print(f"⚠ Sem mais resultados para {nome}")
                    break

                # Clica no resultado atual
                navegador.execute_script("arguments[0].click();", link_resultado)
                # time.sleep(0.5)

                # Percorre fichas e compara data + tipo
                linhas = navegador.find_elements(By.XPATH, "//*[@id='tabelaFichas']/tbody/tr")
                for linha in linhas:
                    try:
                        data_td = linha.find_element(By.XPATH, "./td[1]").text.strip()
                        exame_td = linha.find_element(By.XPATH, "./td[2]").text.strip()

                        if data_td == data and exame_td == exame:
                            link_ficha = linha.find_element(By.XPATH, "./td[1]/a")
                            navegador.execute_script("arguments[0].click();", link_ficha)
                            clicou = True
                            print(f"Clique realizado: {nome} | {exame} | {data} | tr[{indice}]")
                            break
                    except Exception:
                        continue

                if clicou:
                    break

                # Não achou — volta via btn_programa e troca iframe
                print(f"Não bateu em tr[{indice}], tentando tr[{indice+1}]...")
                indice += 1

                navegador.switch_to.default_content()
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="btn_programa"]')
                )).click()
                # time.sleep(0.5)

                iframes = navegador.find_elements(By.TAG_NAME, "iframe")
                navegador.switch_to.default_content()
                navegador.switch_to.frame(iframes[1])
                # time.sleep(0.5)

            except Exception as e:
                print(f"Erro ao processar resultado tr[{indice}]: {e}")
                break
        # ── FIM ───────────────────────────────────────────────────────────────

        if not clicou:
            print(f"⚠ Nenhuma ficha encontrada para {nome} | {exame} | {data}")
            sem_socged.append({"nome": nome, "exame": exame, "data": data})
            continue

        # Fecha overlay de aniversário se aparecer
        try:
            element = wait.until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="idaniversario"]/div[1]/a[1]'))
            )
            navegador.execute_script("arguments[0].click();", element)
            time.sleep(0.5)
            print("Overlay fechado via JS.")
        except Exception:
            pass

        # ── Verifica se o botão SOCGED existe ────────────────────────────────
        try:
            navegador.find_element(By.XPATH, '//*[@id="botoes"]/table/tbody/tr/td[6]/a/img')
            print("  ✔ possui SOCGED")
        except NoSuchElementException:
            sem_socged.append({"nome": nome, "exame": exame, "data": data})
            print(f"  ✘ SEM SOCGED → {nome} | {exame} | {data}")

    except TimeoutException:
        print(f"  ⚠ Timeout: {nome}")
        sem_socged.append({"nome": nome, "exame": exame, "data": data})

# ── Salva XML ─────────────────────────────────────────────────────────────────
raiz = ET.Element("funcionarios_sem_socged")
raiz.set("total", str(len(sem_socged)))

for entry in sem_socged:
    filho = ET.SubElement(raiz, "funcionario")
    filho.text = entry["nome"]

arvore = ET.ElementTree(raiz)
ET.indent(arvore, space="  ")
arvore.write("sem_socged.xml", encoding="utf-8", xml_declaration=True)

print(f"\nTotal sem SOCGED: {len(sem_socged)}")
print("Arquivo 'sem_socged.xml' salvo!")