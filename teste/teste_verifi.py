
from dotenv import load_dotenv
import os

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db import DBHandler, Ficha

load_dotenv()
 
db = DBHandler(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_DATABASE"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)
 
# lista de teste
lista_provedor = [
    Ficha(
        Sequencial_ficha="0000678458",
        Empresa="Empresa ABC",
        Exames="Admissional",
        Funcionario="João Silva",
        Funcao="Operador",
        Turno="Manhã",
        Nascimento="15/03/1990",
        Admissao="01/01/2024",
        Tip_exame="Clínico",
        Dt_ficha="20/03/2026",
        Prest_de_servi="Prestadora X",
    ),
    Ficha(
        Sequencial_ficha="0000678478",
        Empresa="Empresa ABC",
        Exames="Periódico",
        Funcionario="Maria Souza",
        Funcao="Supervisora",
        Turno="Tarde",
        Nascimento="22/07/1985",
        Admissao="15/06/2020",
        Tip_exame="Clínico + Laboratorial",
        Dt_ficha="20/03/2026",
        Prest_de_servi="Prestadora X",
    ),
]
 
with db:
 
    # INSERT em lote
    print("=== INSERT ===")
    relatorio = db.inserir_lista(lista_provedor)
    print("Relatório:", relatorio)
 
    # SELECT todos
    print("\n=== SELECT TODOS ===")
    todos = db.buscar_todos()
    print(f"Total de fichas no banco: {len(todos)}")
    for f in todos:
        print(f)
 
    # SELECT por funcionário
    print("\n=== SELECT POR FUNCIONÁRIO ===")
    fichas_joao = db.buscar_por_funcionario("João Silva")
    print(f"Fichas encontradas: {len(fichas_joao)}")
 
    # UPDATE
    print("\n=== UPDATE ===")
    if relatorio["inseridos"]:
        id_atualizar = relatorio["inseridos"][0]["id"]
        ficha_atualizada = Ficha(
            Sequencial_fic="",
            Empresa="Empresa ABC",
            Exames="Admissional",
            Funcionario="João Silva",
            Funcao="Operador Sênior",       # <- campo alterado
            Turno="Integral",               # <- campo alterado
            Nascimento="15/03/1990",
            Admissao="01/01/2024",
            Tip_exame="Clínico",
            Dt_ficha="20/03/2026",
            Prest_de_servi="Prestadora X",
        )
        db.atualizar(ficha_atualizada)
 
    # VERIFICAÇÃO
    print("\n=== VERIFICAÇÃO ===")
    check = db.verificar_funcionario("João Silva")
    print(f"Status: {check['status']} — {check['total_fichas']} ficha(s) encontrada(s)")
 
    # DELETE
    print("\n=== DELETE ===")
    if relatorio["inseridos"]:
        id_deletar = relatorio["inseridos"][-1]["id"]
        db.deletar(id_deletar)