from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import sqlite3
from reportlab.pdfgen import canvas
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
session_data = {}

# == CONFIGURAÇÕES (Preencha aqui) ==
EMAIL_REMETENTE = "SEU_EMAIL_AQUI@gmail.com"
SENHA_EMAIL = "SUA_SENHA_APP"
ADVOGADO_NOME = "Dr. NOME DO ADVOGADO"
ADVOGADO_CONTATO = "(xx) xxxxx-xxxx"

@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get('Body', '').strip().lower()
    from_number = request.values.get('From', '').split(':')[-1]
    response = MessagingResponse()
    msg = response.message()

    user = session_data.get(from_number, {"step": "inicio"})

    def reset():
        session_data[from_number] = {"step": "inicio"}
        return "👋 Olá! Bem-vindo ao atendimento jurídico. Por favor, escolha uma área:\n1️⃣ Trabalhista\n2️⃣ Previdenciária\n3️⃣ Cível"

    if incoming_msg in ['voltar', 'reiniciar']:
        msg.body(reset())
        return str(response)

    # Início
    if user["step"] == "inicio" or incoming_msg == "oi":
        user["step"] = "area"
        msg.body(reset())
    
    # Área de interesse
    elif user["step"] == "area":
        areas = {"1": "Trabalhista", "2": "Previdenciária", "3": "Cível"}
        if incoming_msg in areas:
            user["area"] = areas[incoming_msg]
            user["step"] = "descricao"
            msg.body(f"📝 Ótimo! Sobre o que exatamente se trata seu caso na área {areas[incoming_msg]}?")
        else:
            msg.body("Escolha uma opção válida:\n1️⃣ Trabalhista\n2️⃣ Previdenciária\n3️⃣ Cível")

    elif user["step"] == "descricao":
        user["descricao"] = incoming_msg
        user["step"] = "comprovacao"
        msg.body("📎 Você tem como comprovar o ocorrido? (sim/não)")

    elif user["step"] == "comprovacao":
        if incoming_msg in ["sim", "não", "nao"]:
            user["tem_comprovacao"] = incoming_msg
            user["step"] = "como_comprova"
            msg.body("🔍 Por meio de quê você pode comprovar? (ex: prints, testemunhas, documentos?)")
        else:
            msg.body("Responda apenas com 'sim' ou 'não'.")

    elif user["step"] == "como_comprova":
        user["como_comprova"] = incoming_msg
        user["step"] = "veridico"
        msg.body("✅ As informações que você está fornecendo são verdadeiras e podem ser usadas legalmente? (sim/não)")

    elif user["step"] == "veridico":
        if incoming_msg in ["sim", "não", "nao"]:
            user["veridico"] = incoming_msg
            user["step"] = "email"
            msg.body("📧 Digite seu e-mail para enviarmos o contrato:")
        else:
            msg.body("Responda apenas com 'sim' ou 'não'.")

    elif user["step"] == "email":
        user["email"] = incoming_msg
        user["step"] = "confirmacao"
        msg.body(f"📄 Tudo pronto! Deseja gerar o contrato com os dados informados? (sim/não)")

    elif user["step"] == "confirmacao":
        if incoming_msg == "sim":
            salvar_em_banco(user, from_number)
            gerar_contrato(user, from_number)
            enviar_email(user)
            msg.body(f"✅ Contrato gerado e enviado para {user['email']}!\n📞 Entre em contato com {ADVOGADO_NOME} no número {ADVOGADO_CONTATO} para prosseguir.\n\nSe quiser reiniciar, digite 'reiniciar'.")
            session_data.pop(from_number)
        else:
            msg.body("❌ Cancelado. Se quiser começar de novo, digite 'reiniciar'.")
            session_data.pop(from_number)
    else:
        msg.body("Não entendi. Para iniciar, envie qualquer mensagem ou 'oi'.")

    session_data[from_number] = user
    return str(response)

# ======= Funções auxiliares ========

def salvar_em_banco(data, telefone):
    conn = sqlite3.connect('clientes.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes (
                    telefone TEXT, area TEXT, descricao TEXT,
                    comprovacao TEXT, meio TEXT, veridico TEXT, email TEXT
                )''')
    c.execute("INSERT INTO clientes VALUES (?, ?, ?, ?, ?, ?, ?)", (
        telefone,
        data["area"],
        data["descricao"],
        data["tem_comprovacao"],
        data["como_comprova"],
        data["veridico"],
        data["email"]
    ))
    conn.commit()
    conn.close()

def gerar_contrato(data, telefone):
    nome_pdf = f"contrato_{telefone}.pdf"
    c = canvas.Canvas(nome_pdf)
    c.drawString(100, 800, "Contrato de Atendimento Jurídico")
    c.drawString(100, 770, f"Área: {data['area']}")
    c.drawString(100, 750, f"Descrição do Caso: {data['descricao']}")
    c.drawString(100, 730, f"Comprovação: {data['tem_comprovacao']} - {data['como_comprova']}")
    c.drawString(100, 710, f"Informações verídicas: {data['veridico']}")
    c.drawString(100, 690, f"E-mail: {data['email']}")
    c.drawString(100, 670, f"Advogado Responsável: {ADVOGADO_NOME}")
    c.save()

def enviar_email(data):
    nome_pdf = f"contrato_{data['email'].replace('@', '_')}.pdf"
    gerar_contrato(data, data['email'].replace('@', '_'))

    msg = EmailMessage()
    msg['Subject'] = 'Contrato Jurídico'
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = data['email']
    msg.set_content("Segue o contrato referente ao seu atendimento jurídico.")

    with open(f"contrato_{data['email'].replace('@', '_')}.pdf", 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=f.name)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_REMETENTE, SENHA_EMAIL)
        smtp.send_message(msg)

# ======= Execução =========
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
