import smtplib
import sys
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
from database.db import DBHandler
 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db import DBHandler
 
load_dotenv()
 
EMAIL_HOST     = 'smtp.gmail.com'
EMAIL_PORT     = 587
EMAIL_USER     = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_DESTINO  = os.getenv('EMAIL_DESTINO')

db = DBHandler(
    host     = os.getenv("DB_HOST"),
    database = os.getenv("DB_DATABASE"),
    user     = os.getenv("DB_USER"),
    password = os.getenv("DB_PASSWORD"),
)

 
 
# ── Monta linhas da tabela ────────────────────────────────────────────────────
def gerar_linhas(fichas):
    linhas = ""
    for i, f in enumerate(fichas, start=1):
        bg    = "#ffffff" if i % 2 == 0 else "#f8fafc"
        borda = "border-bottom:1px solid #e2e8f0;" if i < len(fichas) else ""
        linhas += f"""
        <tr style="background-color:{bg};">
          <td style="padding:13px 16px; font-size:13px; color:#cbd5e1; {borda}">{i}</td>
          <td style="padding:13px 16px; font-size:14px; color:#1e293b; font-weight:500; {borda}">{f['Funcionario']}</td>
          <td style="padding:13px 16px; font-size:13px; color:#475569; {borda}">{f['Tip_exame']}</td>
          <td style="padding:13px 16px; font-size:13px; color:#475569; {borda}">{f['Dt_ficha']}</td>
          <td style="padding:13px 16px; font-size:13px; color:#475569; {borda}">{f['Empresa']}</td>
        </tr>"""
    return linhas
 
 
# ── Monta HTML completo ───────────────────────────────────────────────────────
def gerar_html(fichas):
    total      = len(fichas)
    data_envio = datetime.now().strftime("%d/%m/%Y %H:%M")
 
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"/></head>
<body style="margin:0; padding:40px 0; background-color:#f1f5f9; font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
 
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f1f5f9; padding:40px 0;">
    <tr><td align="center">
      <table width="720" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-radius:10px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,0.08);">
 
        <tr>
          <td style="background-color:#334155; padding:28px 40px;">
            <p style="margin:0 0 4px; color:rgba(255,255,255,0.6); font-size:11px; letter-spacing:2px; text-transform:uppercase;">Aviso Interno</p>
            <h1 style="margin:0; color:#ffffff; font-size:22px; font-weight:700;">Funcionários sem SOCGED</h1>
          </td>
        </tr>
 
        <tr>
          <td style="padding:32px 40px;">
            <p style="margin:0 0 20px; color:#475569; font-size:14px; line-height:1.7;">
              Prezada equipe,<br/><br/>
              Os funcionários listados abaixo estão <strong style="color:#334155;">sem SOCGED</strong> registrado. Por favor, providenciem a regularização o quanto antes.
            </p>
 
            <p style="margin:0 0 20px;">
              <span style="display:inline-block; background-color:#f8fafc; color:#64748b; font-size:12px; font-weight:700; padding:6px 14px; border-radius:20px; border:1px solid #e2e8f0;">
                Total: {total} funcionário(s)
              </span>
            </p>
 
            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden;">
              <thead>
                <tr style="background-color:#f8fafc;">
                  <td style="padding:12px 16px; font-size:11px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.8px; border-bottom:1px solid #e2e8f0; width:40px;">#</td>
                  <td style="padding:12px 16px; font-size:11px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.8px; border-bottom:1px solid #e2e8f0;">Nome</td>
                  <td style="padding:12px 16px; font-size:11px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.8px; border-bottom:1px solid #e2e8f0;">Tipo Exame</td>
                  <td style="padding:12px 16px; font-size:11px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.8px; border-bottom:1px solid #e2e8f0;">Data Ficha</td>
                  <td style="padding:12px 16px; font-size:11px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.8px; border-bottom:1px solid #e2e8f0;">Empresa</td>
                </tr>
              </thead>
              <tbody>
                {gerar_linhas(fichas)}
              </tbody>
            </table>
 
            <p style="margin:28px 0 0; color:#94a3b8; font-size:13px;">
              Em caso de dúvidas, entre em contato com a equipe de suporte.
            </p>
          </td>
        </tr>
 
        <tr>
          <td style="background-color:#f8fafc; padding:18px 40px; border-top:1px solid #e2e8f0;">
            <p style="margin:0; color:#cbd5e1; font-size:12px; text-align:center;">
              © 2026 Clínica Saúde Total · Notificação gerada em {data_envio}
            </p>
          </td>
        </tr>
 
      </table>
    </td></tr>
  </table>
 
</body>
</html>"""
 
 
# ── Envia o email ─────────────────────────────────────────────────────────────
def enviar_email(assunto, html_conteudo):
    try:
        msg = MIMEMultipart("alternative")
        msg['From']    = EMAIL_USER
        msg['To']      = EMAIL_DESTINO
        msg['Subject'] = assunto
        msg.attach(MIMEText(html_conteudo, 'html'))
 
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, EMAIL_DESTINO, msg.as_string())
        server.quit()
        print(f"✅ Email enviado para {EMAIL_DESTINO}.")
    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")
 
 
# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    db = DBHandler(
        host     = os.getenv("DB_HOST"),
        database = os.getenv("DB_DATABASE"),
        user     = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD"),
    )
 
with db:
    fichas = db.buscar_sem_socged()

if not fichas:
    print("Nenhum funcionário sem SOCGED. Nenhum email enviado.")
else:
    print(f"{len(fichas)} funcionário(s) sem SOCGED encontrado(s).")
    html = gerar_html(fichas)  # sua função que monta o HTML a partir da lista

    try:
        # envia um único e-mail com todos os funcionários
        enviar_email("Funcionários sem SOCGED", html)

        # só marca como enviado se o envio foi bem sucedido
        with db:
            for f in fichas:
                # idempotência: checa antes de marcar (caso outro processo já tenha marcado)
                if f.get("email_sent_at"):
                    print(f"[SKIP] id={f['id']} já marcado como enviado")
                    continue
                try:
                    db.marcar_email_enviado(f['id'])
                except Exception as e:
                    # log e continua; importante não interromper o loop
                    print(f"[WARN] falha ao marcar email_sent_at para id={f.get('id')}: {e}")

        print("[MAIL] E-mail enviado e registros marcados como enviados.")
    except Exception as e:
        # não marcar nada se o envio falhar — evita falsos positivos
        print(f"[ERROR] falha ao enviar e-mail: {e}")

    input('\nPressione qualquer tecla para finalizar o programa.')
