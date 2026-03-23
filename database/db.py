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
    Prest_de_servico: str
    Sequencial_ficha: Optional[int] = field(default=None)  # preenchido na verificação (229)
    socged:           Optional[int] = field(default=None)  # 1 = tem | 0 = não tem | None = não verificado

    def validar(self) -> list[str]:
        erros = []

        campos_obrigatorios = {
            "Empresa":          self.Empresa,
            "Exames":           self.Exames,
            "Funcionario":      self.Funcionario,
            "Funcao":           self.Funcao,
            "Nascimento":       self.Nascimento,
            "Admissao":         self.Admissao,
            "Tip_exame":        self.Tip_exame,
            "Dt_ficha":         self.Dt_ficha,
            "Prest_de_servico": self.Prest_de_servico,
        }

        for nome, valor in campos_obrigatorios.items():
            if not valor or not str(valor).strip():
                erros.append(f"Campo obrigatório vazio: {nome}")

        for campo, valor in [("Nascimento", self.Nascimento),
                              ("Admissao",   self.Admissao),
                              ("Dt_ficha",   self.Dt_ficha)]:
            if valor:
                try:
                    datetime.strptime(valor.strip(), "%d/%m/%Y")
                except ValueError:
                    erros.append(f"{campo} com formato inválido: '{valor}' (esperado DD/MM/AAAA)")

        campos_varchar = {
            "Nascimento":       self.Nascimento,
            "Admissao":         self.Admissao,
            "Dt_ficha":         self.Dt_ficha,
            "Prest_de_servico": self.Prest_de_servico,
        }
        for nome, valor in campos_varchar.items():
            if valor and len(str(valor)) > 50:
                erros.append(f"{nome} excede 50 caracteres (atual: {len(str(valor))})")

        return erros


# ──────────────────────────────────────────────
#  DATABASE HANDLER
# ──────────────────────────────────────────────
class DBHandler:

    TABELA = "Tabela_tetes"

    def __init__(self, host: str, database: str, user: str, password: str, port: int = 3306):
        self.config = {
            "host":     host,
            "database": database,
            "user":     user,
            "password": password,
            "port":     port,
        }
        self._conn = None

    # ── conexão ────────────────────────────────
    def conectar(self):
        try:
            self._conn = mysql.connector.connect(**self.config)
            if self._conn.is_connected():
                print(f"[DB] Conectado ao banco '{self.config['database']}'")
        except Error as e:
            raise ConnectionError(f"[DB] Falha ao conectar: {e}")

    def desconectar(self):
        if self._conn and self._conn.is_connected():
            self._conn.close()
            print("[DB] Conexão encerrada")

    def __enter__(self):
        self.conectar()
        return self

    def __exit__(self, *_):
        self.desconectar()

    def _cursor(self):
        if not self._conn or not self._conn.is_connected():
            self.conectar()
        return self._conn.cursor(dictionary=True)

    # ── SELECT ─────────────────────────────────
    def buscar_todos(self) -> List[dict]:
        cur = self._cursor()
        cur.execute(f"SELECT * FROM {self.TABELA}")
        resultados = cur.fetchall()
        cur.close()
        return resultados

    def buscar_nao_verificados(self) -> List[dict]:
        """Retorna fichas onde socged ainda é NULL (não verificadas)."""
        cur = self._cursor()
        cur.execute(f"SELECT * FROM {self.TABELA} WHERE socged IS NULL")
        resultados = cur.fetchall()
        cur.close()
        return resultados

    def buscar_por_funcionario(self, nome: str) -> List[dict]:
        cur = self._cursor()
        cur.execute(
            f"SELECT * FROM {self.TABELA} WHERE Funcionario LIKE %s",
            (f"%{nome}%",)
        )
        resultados = cur.fetchall()
        cur.close()
        return resultados

    def buscar_por_empresa(self, empresa: str) -> List[dict]:
        cur = self._cursor()
        cur.execute(
            f"SELECT * FROM {self.TABELA} WHERE Empresa = %s",
            (empresa,)
        )
        resultados = cur.fetchall()
        cur.close()
        return resultados

    # ── INSERT ─────────────────────────────────
    def inserir(self, ficha: Ficha) -> int:
        """
        Insere ficha da raspagem do 311.
        Sequencial_ficha e socged ficam NULL — preenchidos na verificação.
        """
        erros = ficha.validar()
        if erros:
            raise ValueError(f"[VALIDAÇÃO] Erros:\n  - " + "\n  - ".join(erros))

        sql = f"""
            INSERT INTO {self.TABELA}
                (Empresa, Exames, Funcionario, Funcao, Turno,
                 Nascimento, Admissao, Tip_exame, Dt_ficha, Prest_de_servico,
                 Sequencial_ficha, socged)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, NULL)
        """
        valores = (
            ficha.Empresa, ficha.Exames, ficha.Funcionario, ficha.Funcao,
            ficha.Turno,   ficha.Nascimento, ficha.Admissao, ficha.Tip_exame,
            ficha.Dt_ficha, ficha.Prest_de_servico,
        )
        cur = self._cursor()
        cur.execute(sql, valores)
        self._conn.commit()
        novo_id = cur.lastrowid
        cur.close()
        print(f"[INSERT] {ficha.Funcionario} inserido")
        return novo_id

    def inserir_lista(self, fichas: List[Ficha]) -> dict:
        inseridos, erros = [], []
        for i, ficha in enumerate(fichas):
            try:
                novo_id = self.inserir(ficha)
                inseridos.append({"index": i, "funcionario": ficha.Funcionario, "id": novo_id})
            except (ValueError, Error) as e:
                erros.append({"index": i, "funcionario": ficha.Funcionario, "erro": str(e)})
        print(f"\n[LOTE] Inseridos: {len(inseridos)} | Erros: {len(erros)}")
        return {"inseridos": inseridos, "erros": erros}

    # ── UPDATE verificação ──────────────────────
    def atualizar_verificacao(self, funcionario: str, dt_ficha: str, tip_exame: str,
                               sequencial_ficha: int, socged: int) -> bool:
        """
        Chamado pela verificacao_270.py após conferir no 229.
        Usa Funcionario + Dt_ficha + Tip_exame como chave pois Sequencial_ficha
        ainda é NULL no banco nesse momento.
        Salva o Sequencial_ficha coletado na ficha aberta e o resultado do SOCGED (1 ou 0).
        """
        sql = f"""
            UPDATE {self.TABELA}
            SET Sequencial_ficha = %s,
                socged           = %s
            WHERE Funcionario = %s
              AND Dt_ficha    = %s
              AND Tip_exame   = %s
              AND socged IS NULL
        """
        cur = self._cursor()
        cur.execute(sql, (sequencial_ficha, socged, funcionario, dt_ficha, tip_exame))
        self._conn.commit()
        alterado = cur.rowcount > 0
        cur.close()
        status = "✔ tem SOCGED" if socged == 1 else "✘ sem SOCGED"
        print(f"[UPDATE] {funcionario} | seq {sequencial_ficha} | {status}")
        return alterado

    # ── UPDATE geral ────────────────────────────
    def atualizar(self, ficha: Ficha) -> bool:
        if ficha.Sequencial_ficha is None:
            raise ValueError("[UPDATE] Sequencial_ficha é obrigatório para atualizar.")

        erros = ficha.validar()
        if erros:
            raise ValueError(f"[VALIDAÇÃO] Erros:\n  - " + "\n  - ".join(erros))

        sql = f"""
            UPDATE {self.TABELA} SET
                Empresa          = %s,
                Exames           = %s,
                Funcionario      = %s,
                Funcao           = %s,
                Turno            = %s,
                Nascimento       = %s,
                Admissao         = %s,
                Tip_exame        = %s,
                Dt_ficha         = %s,
                Prest_de_servico = %s
            WHERE Sequencial_ficha = %s
        """
        valores = (
            ficha.Empresa, ficha.Exames, ficha.Funcionario, ficha.Funcao,
            ficha.Turno,   ficha.Nascimento, ficha.Admissao, ficha.Tip_exame,
            ficha.Dt_ficha, ficha.Prest_de_servico, ficha.Sequencial_ficha,
        )
        cur = self._cursor()
        cur.execute(sql, valores)
        self._conn.commit()
        alterado = cur.rowcount > 0
        cur.close()
        print(f"[UPDATE] {ficha.Sequencial_ficha} — {'atualizado' if alterado else 'não encontrado'}")
        return alterado

    # ── DELETE ──────────────────────────────────
    def deletar(self, sequencial_ficha: int) -> bool:
        cur = self._cursor()
        cur.execute(
            f"DELETE FROM {self.TABELA} WHERE Sequencial_ficha = %s",
            (sequencial_ficha,)
        )
        self._conn.commit()
        deletado = cur.rowcount > 0
        cur.close()
        print(f"[DELETE] {sequencial_ficha} — {'removido' if deletado else 'não encontrado'}")
        return deletado
