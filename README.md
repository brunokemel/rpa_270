# RPA Envio 270 Cobrança ASO

Este projeto é uma automação em Python usando Selenium para RPA de envio da 270 de cobrança ASO no sistema SOC.

## Configuração

1. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

2. Configure o arquivo `.env` com suas credenciais.

3. Execute o script:
   ```
   python main.py
   ```

## Funcionalidades

- Verifica se há dados de exame no banco de dados.
- Se não houver, envia email solicitando a imagem do exame.
- Se houver, acessa o site SOC via Selenium para processar o envio.

## Notas

- Ajuste os seletores no Selenium conforme a estrutura real do site.
- Configure as credenciais de email no código.
- Preencha as informações do banco de dados no `.env`.



<!-- 
# teste tratamento de condicao de pular
# pular_ate = "VALDINEIA NEVES PEIXOTO"  # Passo 1
# encontrado = False     -->


 <!-- # if not encontrado:          # ← e esse bloco passo 2
    #     if nome == pular_ate:
    #         encontrado = True
    #     else:
    #         print(f"Pulando: {nome}")
    #         continue -->