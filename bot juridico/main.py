from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Dicionário simples para simular estado da conversa
usuarios = {}

@app.route('/bot', methods=['POST'])
def bot():
    msg = request.form.get('Body').strip()
    numero = request.form.get('From')
    resp = MessagingResponse()
    resposta = resp.message()

    estado = usuarios.get(numero, {'etapa': 'inicio'})

    if estado['etapa'] == 'inicio':
        resposta.body("👋 Olá! Bem-vindo ao atendimento jurídico.\nEscolha uma área:\n1️⃣ Trabalhista\n2️⃣ Previdenciária\n3️⃣ Consumidor")
        estado['etapa'] = 'area'

    elif estado['etapa'] == 'area':
        if msg == '1':
            resposta.body("Ótimo! Sobre o que é o seu caso trabalhista?\n1️⃣ Demissão sem justa causa\n2️⃣ Horas extras não pagas\n3️⃣ Trabalho sem carteira")
            estado['area'] = 'trabalhista'
            estado['etapa'] = 'trabalhista_opcao'
        else:
            resposta.body("Área ainda não implementada. Por favor, envie '1' para continuar com Trabalhista.")

    elif estado['etapa'] == 'trabalhista_opcao':
        estado['subarea'] = msg
        resposta.body("Quantos anos você trabalhou na empresa?")
        estado['etapa'] = 'anos'

    elif estado['etapa'] == 'anos':
        estado['anos'] = int(msg)
        resposta.body("Qual era seu salário mensal (em R$)?")
        estado['etapa'] = 'salario'

    elif estado['etapa'] == 'salario':
        salario = float(msg)
        estado['salario'] = salario

        aviso = salario
        ferias = salario + (salario / 3)
        fgts = salario * 0.8 * estado['anos']  # Simples estimativa

        total = aviso + ferias + fgts

        estado['valores'] = total

        resposta.body(f"📊 Estimativa dos seus direitos:\n"
                      f"- Aviso prévio: R${aviso:.2f}\n"
                      f"- Férias + 1/3: R${ferias:.2f}\n"
                      f"- FGTS + multa: R${fgts:.2f}\n"
                      f"💰 Total aproximado: R${total:.2f}\n\n"
                      f"Deseja gerar um contrato para prosseguir com o processo? (Sim/Não)")
        estado['etapa'] = 'contrato'

    elif estado['etapa'] == 'contrato':
        if msg.lower() == 'sim':
            resposta.body("✅ Perfeito! Envie seu nome completo e CPF para gerarmos o contrato.")
            estado['etapa'] = 'dados_contrato'
        else:
            resposta.body("Entendido. Estaremos à disposição para qualquer dúvida.")
            estado['etapa'] = 'fim'

    elif estado['etapa'] == 'dados_contrato':
        resposta.body("📄 Seu contrato foi enviado para análise. Um advogado entrará em contato em breve.")
        estado['etapa'] = 'fim'

    else:
        resposta.body("Digite 'oi' para começar novamente.")

    usuarios[numero] = estado
    return str(resp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
