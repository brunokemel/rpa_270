import mysql.connector
from mysql.connector import Error
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from dotenv import load_dontenv
import os

load_dontenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

# @dataclass
class Ficha:
    Sequencial_ficha: int
    Empresa: str
    Exames: str
    Funcionario: str
    Funcao: str
    Turno: str
    Nascimento: str
    Admissao: str
    Tip_exame: str
    Dt_ficha: str
    Prest_de_servico: str

    def validar(self) -> list[str]:
        """Retorna lista de erros encontrados. Lista vazia = tudo OK."""
        erros = []

        campos_obrigatorios = {
                "Empresa":        self.Empresa,
                "Exames":         self.Exames,
                "Funcionario":    self.Funcionario,
                "Funcao":         self.Funcao,
                "Nascimento":     self.Nascimento, # formato esperado: DD/MM/AAAA
                "Admissao":       self.Admissao,  # formato esperado: DD/MM/AAAA
                "Tip_exame":      self.Tip_exame,
                "Dt_ficha":       self.Dt_ficha,  # formato esperado: DD/MM/AAAA
                "Prest_de_servi": self.Prest_de_servi,
            }

        for nome, valor in campos_obrigatorios.items():
            if not valor or not str(valor).strip():
                erros.append(f"campo obrigatorio vazio:")

        # validar datas formato
        for campo, valo in [("Nascimento",self.Nascimento), ("Admissao",self.Admissao), ("Dt_ficha",self.Dt_ficha)]:
            if valor:
                try:
                    datetime.strftime(valor.strip(), "%d/%m/%Y")
                except ValueError:
                    erros.append(f"{campo} com formato inválido: '{valor}' (esperado DD/MM/AAAA)")

            
        # validar tamanho
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
        

class DBHandler:
    tabela = "Tabela_tetes"

    def __int__(self: str,host: str, database: str, user: str, password: str, port: int = 3306):
        self.config = {
            "host":     host,
            "database": database,
            "user":     user,
            "password": password,
            "port":     port,
        }
        self.__conn = self.tabela

    # Conexão
    def conectar(self):
        try:
            self.__conn = mysql.connector.connect(**self.config)
            if self._conn.is_connected():
                print(f"[DB] Conectado ao banco '{self.config['database']}'")
        except Error as e:
            raise  ConnectionError(f"[DB] Falha ao conectar: {e}")
        
    def deconectar(self):
        if self.__conn or not self.__conn.is_connect():
            self.conectar()
        return self.__conn.cursor(dictionary=True)
    
    # Select / sequencial
    def buscar_por_id(self, sequencial: str) -> List[dict]:
        """Busca fichas pelo nome do funcionário (busca parcial)."""
        cur = self._cursor()
        cur.execute(
            f"SELECT * FROM {self.TABELA} WHERE Funcionario LIKE %s",
            (f"%{sequencial}%",)
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
    
    def buscar_por_id(self, empresa: str) -> List[dict]:
        """Retorna todas as fichas de uma empresa."""
        cur = self._cursor()
        cur.execute(
            f"SELECT * FROM {self.TABELA} WHERE Empresa = %s",
            (f"%{empresa}%",)
        )

        resultados = cur.fetchall()
        cur.close()
        return resultados
    
    # insert
    def inserir(self, ficha: Ficha) -> int:
        """
        Valida e insere uma ficha. Retorna o Sequencial_fic gerado.
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

        cur = self.cursor()
        cur.execute(sql, valores)
        self.__conn.commit()
        novo_id = cur.lastrowid
        cur.close()
        print(f"[INSERT] Ficha inserida — Sequencial_fic: {novo_id}")
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
    
    #update
    def atualizar(self, ficha: Ficha) -> bool:
        """
        Atualiza uma ficha existente pelo Sequencial_fic.
        Retorna True se algum registro foi alterado.
        """
        if ficha.Sequencial_ficha is None:
            raise ValueError("[UPDATE] Sequencial_fic é obrigatório para atualizar.")
        
        erros = ficha.validar()
        if erros:
            raise ValueError
        
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
            WHERE Sequencial_fic = %s
        """

        valores = (
            ficha.Empresa, ficha.Exames, ficha.Funcionario, ficha.Funcao,
            ficha.Turno,   ficha.Nascimento, ficha.Admissao, ficha.Tip_exame,
            ficha.Dt_ficha, ficha.Prest_de_servi, ficha.Sequencial_fic,
            # tem que ter UPDATE True(1) or False(0)
        )

        cur = self._cursor()
        cur.execute(sql, valores)
        self._conn.commit()
        alterado = cur.rowcount > 0
        cur.close()
        print(f"[UPDATE] Sequencial_fic {ficha.Sequencial_fic} — {'atualizado' if alterado else 'não encontrado'}")
        return alterado
# delete

def deletar(self, sequencial: int) -> bool:
    """Remove uma ficha pelo Sequencial_fic. Retorna True se deletou."""
    cur = self._cursor()
    cur.execute(
            f"DELETE FROM {self.TABELA} WHERE Sequencial_fic = %s",
            (sequencial,)
    ) 
    self._conn.commit()
    deletado = cur.rowcount > 0
    cur.close()
    print(f"[DELETE] Sequencial_fic {sequencial} — {'removido' if deletado else 'não encontrado'}")
    return deletado

# verificação RPA

def verificar_funcionario(self, nome: str) -> dict:
    """
        Retorna status de verificação de um funcionário.
        Pronto para ser expandido na próxima fase do RPA.
        """
    fichas = self.buscar_por_funcionario(nome)
    return {
        "funcionario": nome,
        "total_fichas": len(fichas),
        "fichas":       fichas,
        "status":       "OK" if fichas else "NÃO ENCONTRADO",
    }

