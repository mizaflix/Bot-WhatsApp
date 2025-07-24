from flask import Flask, request, send_from_directory
from twilio.twiml.messaging_response import MessagingResponse
from reportlab.pdfgen import canvas
import os
from datetime import datetime

app = Flask(__name__)
# Pasta onde os contratos serão salvos
CONTRACT_FOLDER = 'contratos'
os.makedirs(CONTRACT_FOLDER, exist_ok=True)

# Dicionário para armazenar o estado de cada usuário
users = {}

# Opções por área
areas = {
    "Trabalhista": ["Demissão sem justa causa", "Horas extras não pagas", "Acidente de trabalho", "Assédio moral", "Férias não pagas"],
    "Previdenciária": ["Aposentadoria por idade", "Aposentadoria por invalidez", "Auxílio-doença", "Pensão por morte"],
    "Cível": ["Cobrança indevida", "Nome negativado indevidamente", "Problema com imóvel"],
    "Família": ["Pensão alimentícia", "Guarda de filhos", "Divórcio"]
}

# Espaços personalizáveis
ADVOGADO_NOME = "[NOME DO ADVOGADO AQUI]"
ADVOGADO_NUMERO = "[NUMERO DO ADVOGADO AQUI]"

@app.route('/contratos/<filename>')
def contrato(filename):
    return send_from_directory(CONTRACT_FOLDER, filename)

@app.route('/', methods=['POST'])
def bot():
    sender = request.form['From']
    msg = request.form['Body'].strip()
    resp = MessagingResponse()
    user = users.get(sender, {'step': 0})

    step = user['step']

    if msg.lower() in ["início", "recomeçar"]:
        users[sender] = {'step': 0}
        resp.message("✅ Conversa reiniciada. Digite qualquer coisa para começar.")
        return str(resp)

    if step == 0:
        user['step'] = 1
        users[sender] = user
        area_list = "\n".join([f"- {a}" for a in areas])
        resp.message(f"Olá! Qual a área jurídica do seu interesse?\n{area_list}\n\nDigite exatamente como está.")

    elif step == 1:
        if msg in areas:
            user['area'] = msg
            user['step'] = 2
            users[sender] = user
            opcoes = areas[msg]
            texto = "\n".join([f"- {op}" for op in opcoes])
            resp.message(f"Entendi! Sobre o que se trata especificamente?\n{texto}\n\nDigite exatamente como está.")
        else:
            resp.message("Área inválida. Por favor, digite uma das opções corretamente.")

    elif step == 2:
        if msg in areas.get(user['area'], []):
            user['caso'] = msg
            user['step'] = 3
            users[sender] = user
            resp.message("Você tem como comprovar isso? (Sim ou Não)")
        else:
            resp.message("Opção inválida. Digite exatamente como uma das opções anteriores.")

    elif step == 3:
        if msg.lower() in ["sim", "não"]:
            user['tem_comprovante'] = msg
            user['step'] = 4
            users[sender] = user
            resp.message("Por meio de quê você pode comprovar? (ex: holerite, testemunha, laudo médico...)")
        else:
            resp.message("Responda apenas com 'Sim' ou 'Não'.")

    elif step == 4:
        user['meio'] = msg
        user['step'] = 5
        users[sender] = user
        resp.message("Tudo isso é verídico? (Sim ou Não)")

    elif step == 5:
        if msg.lower() in ["sim", "não"]:
            user['veracidade'] = msg
            user['step'] = 6
            users[sender] = user
            resp.message("Baseado em seu caso, você tem direito a valores entre R$5.000 a R$25.000. Deseja prosseguir com a geração do contrato? (Sim ou Não)")
        else:
            resp.message("Responda com 'Sim' ou 'Não'.")

    elif step == 6:
        if msg.lower() == "sim":
            filename = f"contrato-{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            filepath = os.path.join(CONTRACT_FOLDER, filename)
            c = canvas.Canvas(filepath)
            c.drawString(100, 800, f"Contrato Jurídico - Área: {user['area']}")
            c.drawString(100, 780, f"Caso: {user['caso']}")
            c.drawString(100, 760, f"Tem comprovante: {user['tem_comprovante']}")
            c.drawString(100, 740, f"Meio de comprovação: {user['meio']}")
            c.drawString(100, 720, f"Veracidade: {user['veracidade']}")
            c.drawString(100, 700, f"Assinado virtualmente em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            c.drawString(100, 680, f"Advogado responsável: {ADVOGADO_NOME}")
            c.save()

            url = f"{request.url_root}contratos/{filename}"
            user['step'] = 7
            users[sender] = user
            resp.message(f"✅ Contrato gerado com sucesso! Acesse aqui:\n{url}")
            resp.message(f"Entre em contato com o advogado para dar continuidade: {ADVOGADO_NUMERO}")
        else:
            resp.message("Ok, processo encerrado. Se quiser reiniciar, digite 'início'.")
            users[sender] = {'step': 0}

    else:
        resp.message("Digite 'início' para começar uma nova conversa.")
        users[sender] = {'step': 0}

    return str(resp)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
