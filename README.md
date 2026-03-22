# RPA 270 — Cobrança ASO 🤖

Automação em Python com Selenium para envio da **270 de cobrança ASO** no sistema **SOC**.

O RPA busca os dados de exames no banco de dados MySQL, verifica se estão completos e processa o envio automaticamente. Caso falte alguma informação, envia um e-mail solicitando a imagem do exame.

---

## 📋 Fluxo do RPA

```
Banco de dados (MySQL)
        │
        ▼
Há dados de exame?
   ├── NÃO → Envia e-mail solicitando imagem (mail.py)
   └── SIM → Acessa SOC via Selenium e processa envio (main.py)
```

---

## 🗂️ Estrutura

```
rpa_270/
├── main.py              # Orquestrador principal do RPA
├── raspagem_270.py      # Raspagem/coleta dos dados do provedor
├── mail.py              # Envio de e-mail quando falta imagem de exame
├── index.html           # Interface de apoio
├── db/                  # Módulos de banco de dados (SELECT, INSERT, UPDATE)
├── teste/               # Scripts de teste
├── requirements.txt     # Dependências do projeto
├── anotacoes.md         # Anotações de desenvolvimento
└── .gitignore
```

---

## 🗃️ Tabela no banco

| Campo | Tipo |
|---|---|
| Sequencial_fic | INT (PK) |
| Empresa | TEXT |
| Exames | TEXT |
| Funcionario | TEXT |
| Funcao | TEXT |
| Turno | VARCHAR(50) |
| Nascimento | VARCHAR(50) |
| Admissao | VARCHAR(50) |
| Tip_exame | TEXT |
| Dt_ficha | VARCHAR(50) |
| Prest_de_servi | VARCHAR(50) |

---

## ⚙️ Instalação

```bash
pip install -r requirements.txt
```

Dependências: `selenium`, `webdriver-manager`, `python-dotenv`, `pymysql`

---

## 🔧 Configuração

Crie um arquivo `.env` na raiz com as credenciais:

```env
DB_HOST=localhost
DB_NAME=nome_do_banco
DB_USER=root
DB_PASSWORD=sua_senha

EMAIL_USER=seu@email.com
EMAIL_PASSWORD=sua_senha
```

---

## ▶️ Como rodar

```bash
python main.py
```

---

## 🔜 Próxima etapa

Conferência no sistema SOC se cada funcionário está com todos os dados corretos.
