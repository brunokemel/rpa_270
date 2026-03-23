import mysql.connector
from mysql.connector import Error
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()


# ──────────────────────────────────────────────
#  MODEL
# ──────────────────────────────────────────────
@dataclass
class Ficha:
    Empresa:          str
    Exames:           str
    Funcionario:      str
    Funcao:           str
    Turno:            str
    Nascimento:       str          # formato esperado: DD/MM/AAAA
    Admissao:         str          # formato esperado: DD/MM/AAAA
    Tip_exame:        str
    Dt_ficha:         str          # formato esperado: DD/MM/AAAA
    Prest_de_servi:   str
    Sequencial_ficha: int   # PK, puxado do SOC

    def validar(self) -> list[str]:
        """Retorna lista de erros encontrados. Lista vazia = tudo OK."""
        erros = []

        # Sequencial_ficha obrigatório — vem do SOC
        if not self.Sequencial_ficha:
            erros.append("Campo obrigatório vazio: Sequencial_ficha (deve vir do SOC)")

        campos_obrigatorios = {
            "Empresa":        self.Empresa,
            "Exames":         self.Exames,
            "Funcionario":    self.Funcionario,
            "Funcao":         self.Funcao,
            "Nascimento":     self.Nascimento,
            "Admissao":       self.Admissao,
            "Tip_exame":      self.Tip_exame,
            "Dt_ficha":       self.Dt_ficha,
            "Prest_de_servi": self.Prest_de_servi,  # FIX: nome correto do campo
        }

        for nome, valor in campos_obrigatorios.items():
            if not valor or not str(valor).strip():
                erros.append(f"Campo obrigatório vazio: {nome}")

        # FIX: variável do loop era 'valo' em vez de 'valor'
        for campo, valor in [("Nascimento", self.Nascimento),
                              ("Admissao",   self.Admissao),
                              ("Dt_ficha",   self.Dt_ficha)]:
            if valor:
                try:
                    datetime.strptime(valor.strip(), "%d/%m/%Y")
                except ValueError:
                    erros.append(f"{campo} com formato inválido: '{valor}' (esperado DD/MM/AAAA)")

        # Validar tamanho VARCHAR(50)
        campos_varchar = {
            "Nascimento":     self.Nascimento,
            "Admissao":       self.Admissao,
            "Dt_ficha":       self.Dt_ficha,
            "Prest_de_servi": self.Prest_de_servi,
        }
        for nome, valor in campos_varchar.items():
            if valor and len(str(valor)) > 50:
                erros.append(f"{nome} excede 50 caracteres (atual: {len(str(valor))})")

        return erros



#  DATABASE HANDLER
class DBHandler:

    TABELA = "Tabela_tetes"   # FIX: era 'tabela' minúsculo, padronizado para TABELA

    def __init__(self, host: str, database: str, user: str, password: str, port: int = 3306):
        self.config = {
            "host":     host,
            "database": database,
            "user":     user,
            "password": password,
            "port":     port,
        }
        self._conn = None   # FIX: era self._conn = self.tabela (string!)

    # conexão 
    def conectar(self):
        try:
            self._conn = mysql.connector.connect(**self.config)
            if self._conn.is_connected():
                print(f"[DB] Conectado ao banco '{self.config['database']}'")
        except Error as e:
            raise ConnectionError(f"[DB] Falha ao conectar: {e}")

    def desconectar(self):   # FIX: era 'deconectar' + lógica completamente errada
        if self._conn and self._conn.is_connected():
            self._conn.close()
            print("[DB] Conexão encerrada")

    # FIX: __enter__ e __exit__ ausentes — necessários para 'with db:'
    def __enter__(self):
        self.conectar()
        return self

    def __exit__(self, *_):
        self.desconectar()

    # ── helper interno 
    def _cursor(self):
        if not self._conn or not self._conn.is_connected():
            self.conectar()
        return self._conn.cursor(dictionary=True)

    # ── SELECT
    def buscar_todos(self) -> List[dict]:
        """Retorna todos os registros da tabela."""
        cur = self._cursor()
        cur.execute(f"SELECT * FROM {self.TABELA}")
        resultados = cur.fetchall()
        cur.close()
        return resultados

    def buscar_por_id(self, sequencial: int) -> Optional[dict]:
        """Busca uma ficha pelo Sequencial_ficha."""
        cur = self._cursor()
        cur.execute(
            f"SELECT * FROM {self.TABELA} WHERE Sequencial_ficha = %s",
            (sequencial,)
        )
        resultado = cur.fetchone()
        cur.close()
        return resultado

    def buscar_por_funcionario(self, nome: str) -> List[dict]:
        """Busca fichas pelo nome do funcionário (busca parcial)."""
        cur = self._cursor()
        cur.execute(
            f"SELECT * FROM {self.TABELA} WHERE Funcionario LIKE %s",
            (f"%{nome}%",)
        )
        resultados = cur.fetchall()
        cur.close()
        return resultados

    # FIX: renomeado de buscar_por_id (duplicado) para buscar_por_empresa
    def buscar_por_empresa(self, empresa: str) -> List[dict]:
        """Retorna todas as fichas de uma empresa."""
        cur = self._cursor()
        cur.execute(
            f"SELECT * FROM {self.TABELA} WHERE Empresa = %s",
            (empresa,)
        )
        resultados = cur.fetchall()
        cur.close()
        return resultados

    # ── INSERT
    def inserir(self, ficha: Ficha) -> int:
        """
        Valida e insere uma ficha. Retorna o Sequencial_ficha gerado.
        Lança ValueError se houver erros de validação.
        """
        erros = ficha.validar()
        if erros:
            raise ValueError(f"[VALIDAÇÃO] Erros encontrados:\n  - " + "\n  - ".join(erros))

        sql = f"""
            INSERT INTO {self.TABELA}
                (Empresa, Exames, Funcionario, Funcao, Turno,
                 Nascimento, Admissao, Tip_exame, Dt_ficha, Prest_de_servi)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        valores = (
            ficha.Empresa, ficha.Exames, ficha.Funcionario, ficha.Funcao,
            ficha.Turno,   ficha.Nascimento, ficha.Admissao, ficha.Tip_exame,
            ficha.Dt_ficha, ficha.Prest_de_servi,
        )
        cur = self._cursor()   # FIX: era self.cursor() sem underscore
        cur.execute(sql, valores)
        self._conn.commit()
        novo_id = cur.lastrowid
        cur.close()
        print(f"[INSERT] Ficha inserida — Sequencial_ficha: {novo_id}")
        return novo_id

    def inserir_lista(self, fichas: List[Ficha]) -> dict:
        """
        Processa uma lista de fichas do provedor.
        Retorna relatório: { 'inseridos': [...], 'erros': [...] }
        """
        inseridos, erros = [], []

        for i, ficha in enumerate(fichas):
            try:
                novo_id = self.inserir(ficha)
                inseridos.append({"index": i, "funcionario": ficha.Funcionario, "id": novo_id})
            except (ValueError, Error) as e:
                erros.append({"index": i, "funcionario": ficha.Funcionario, "erro": str(e)})

        print(f"\n[LOTE] Inseridos: {len(inseridos)} | Erros: {len(erros)}")
        return {"inseridos": inseridos, "erros": erros}

    # ── UPDATE
    def atualizar(self, ficha: Ficha) -> bool:
        """
        Atualiza uma ficha existente pelo Sequencial_ficha.
        Retorna True se algum registro foi alterado.
        """
        if ficha.Sequencial_ficha is None:
            raise ValueError("[UPDATE] Sequencial_ficha é obrigatório para atualizar.")

        erros = ficha.validar()
        if erros:
            # FIX: raise ValueError sem mensagem não mostrava nada
            raise ValueError(f"[VALIDAÇÃO] Erros encontrados:\n  - " + "\n  - ".join(erros))

        sql = f"""
            UPDATE {self.TABELA} SET
                Empresa        = %s,
                Exames         = %s,
                Funcionario    = %s,
                Funcao         = %s,
                Turno          = %s,
                Nascimento     = %s,
                Admissao       = %s,
                Tip_exame      = %s,
                Dt_ficha       = %s,
                Prest_de_servi = %s
            WHERE Sequencial_ficha = %s
        """
        valores = (
            ficha.Empresa, ficha.Exames, ficha.Funcionario, ficha.Funcao,
            ficha.Turno,   ficha.Nascimento, ficha.Admissao, ficha.Tip_exame,
            ficha.Dt_ficha, ficha.Prest_de_servi, ficha.Sequencial_ficha,
        )
        cur = self._cursor()
        cur.execute(sql, valores)
        self._conn.commit()
        alterado = cur.rowcount > 0
        cur.close()
        print(f"[UPDATE] Sequencial_ficha {ficha.Sequencial_ficha} — {'atualizado' if alterado else 'não encontrado'}")
        return alterado

    # ── DELETE
    # FIX: estava fora da classe (sem indentação)
    def deletar(self, sequencial: int) -> bool:
        """Remove uma ficha pelo Sequencial_ficha. Retorna True se deletou."""
        cur = self._cursor()
        cur.execute(
            f"DELETE FROM {self.TABELA} WHERE Sequencial_ficha = %s",
            (sequencial,)
        )
        self._conn.commit()
        deletado = cur.rowcount > 0
        cur.close()
        print(f"[DELETE] Sequencial_ficha {sequencial} — {'removido' if deletado else 'não encontrado'}")
        return deletado

    # ── VERIFICAÇÃO
    # FIX: estava fora da classe (sem indentação)
    def verificar_funcionario(self, nome: str) -> dict:
        """
        Retorna status de verificação de um funcionário.
        Pronto para ser expandido na próxima fase do RPA.
        """
        fichas = self.buscar_por_funcionario(nome)
        return {
            "funcionario":  nome,
            "total_fichas": len(fichas),
            "fichas":       fichas,
            "status":       "OK" if fichas else "NÃO ENCONTRADO",
        }
