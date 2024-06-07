from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
import os

#importa as funções de análise
from analise_portaria import *


# Define o caminho base como o diretório atual onde o script está sendo executado
base_directory = os.getcwd()

# Configura o diretório de templates e uploads usando caminhos relativos

# Configuração inicial do Flask
app = Flask(__name__, template_folder=os.path.join(base_directory, 'templates'))
app.config['UPLOAD_FOLDER'] = os.path.join(base_directory, 'uploads')



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            resposta = portaria_prosaude(filepath, Verbose=True)  # Função que analisa o arquivo usando LLMs
            #resposta = portaria_prosaude(filepath, Verbose=True, MedRobot=False)  # Função que analisa o arquivo usando LLMs
            resposta_html = formatar_resposta_html(resposta)
            return resposta_html
        else:
            return "Nenhum arquivo enviado."
    else:
        return render_template('resultado.html')

#Função que formata as respostas em um HTML 
def formatar_resposta_html(resposta):
    if isinstance(resposta, dict):
        # Início da formatação HTML
        resultado_html = "<h3>Informações Gerais</h3>"
        #resultado_html += f"<p>Indenização por danos morais ou materiais: {'Sim' if resposta['indenizacao'] else 'Não'}</p>"
        resultado_html += f"<p>Indenização por danos morais ou materiais: N/A</p>"
        resultado_html += f"<p>Condenação em Honorários superior a R$1500: {'Sim' if resposta['condenacao_honorarios'] else 'Não'}</p>"
        #resultado_html += f"<p>Laudo Público: {'Sim' if resposta['laudo_publico'] else 'Não'}</p>"
        resultado_html += f"<p>Laudo Público: Não foi possível determinar.</p>"
        #resultado_html += f"<p>Valor total do tratamento: R$ {resposta['valor_teto']}</p>"
        resultado_html += f"<p>Valor total do tratamento: {resposta['valor_teto']}</p>"
        #resultado_html += f"<p>Respeita valor do teto: {'Sim' if resposta['respeita_valor_teto'] else 'Não'}</p>"
        resultado_html += f"<p>Respeita valor do teto: {'Sim' if resposta['respeita_valor_teto'] else 'Não'}</p>"

        # Formatação para medicamentos
        resultado_html += "<h3>Lista de Medicamentos - Inciso I</h3><ul>"
        
        if not resposta['lista_medicamentos']:
            resultado_html += f"<p> Não há medicamentos na sentença </p>"
        #for medicamento in resposta['lista_medicamentos']:
        #    resultado_html += f"<li>{medicamento['nome_principio']} ({medicamento['nome_comercial']}) - Dosagem: {medicamento['dosagem']}, Registro ANVISA: {medicamento['registro_anvisa']}, Oferta SUS: {'Sim' if medicamento['oferta_SUS'] else 'Não'}, Preço PMVG: R$ {medicamento['preco_PMVG']}, Preço PMVG Máximo: R$ {medicamento['preco_PMVG_max']}</li>"
        #resultado_html += "</ul>"
        for medicamento in resposta['lista_medicamentos']:
            resultado_html += f"<p>{medicamento['nome_principio']} ({medicamento['nome_comercial']}) </p>"
            resultado_html += f"<p>Nome extraído da sentença: {medicamento['nome_extraido']}</p>"
            resultado_html += f"<p>Dose: {medicamento['dosagem']}, Registro ANVISA: {medicamento['registro_anvisa']}, Oferta SUS: {'Sim' if medicamento['oferta_SUS'] else 'Não'}, Preço PMVG: {medicamento['preco_PMVG']}</p>"
            resultado_html += f"<br>"           
        resultado_html += "</ul>"

        
        resultado_html += f"<p>Possui outros itens além de medicamentos: {'Sim' if resposta['possui_outros'] else 'Não'}</p>"
        
        # Formatação para medicamentos
        resultado_html += "<h3>Lista de Outros Itens</h3><ul>"
        
        if not resposta['lista_outros']:
            resultado_html += f"<p> Não há itens na sentença que não sejam medicamentos </p>"
        
        for outro in resposta['lista_outros']:
            resultado_html += f"<p>Padrão Encontrado: {outro}</p>"   
        resultado_html += "</ul>"
        
        """
        # Formatação para intervenções
        resultado_html += "<h3>Intervenções Médicas  - Inciso II</h3><ul>"
        for intervencao in resposta['lista_intervencoes']:
            resultado_html += f"<li>{intervencao['tipo_intervencao']} - Autorizada: {'Sim' if intervencao['autorizada'] else 'Não'}</li>"
        resultado_html += "</ul>"

        # Formatação para compostos
        resultado_html += "<h3>Compostos Alimentares - Inciso III</h3><ul>"
        for composto in resposta['lista_compostos']:
            resultado_html += f"<li>{composto['nome_composto']} - Registro ANVISA: {composto['registro_anvisa']}</li>"
        resultado_html += "</ul>"

        # Formatação para glicêmicos
        resultado_html += "<h3>Índice Glicêmico - Inciso IV</h3><ul>"
        for glicemico in resposta['lista_glicemico']:
            resultado_html += f"<li>{glicemico['tipo_glicemico']} - Autorizada: {'Sim' if glicemico['autorizada'] else 'Não'}</li>"
        resultado_html += "</ul>"

        # Formatação para insumos
        resultado_html += "<h3>Insumos  - Inciso V</h3><ul>"
        for insumo in resposta['lista_insumos']:
            resultado_html += f"<li>{insumo['tipo_insumo']} - Autorizada: {'Sim' if insumo['autorizada'] else 'Não'}</li>"
        resultado_html += "</ul>"

        # Formatação para tratamentos
        resultado_html += "<h3>Tratamentos - Inciso VI</h3><ul>"
        for tratamento in resposta['lista_tratamento']:
            resultado_html += f"<li>{tratamento['tipo_tratamento']} - Autorizada: {'Sim' if tratamento['autorizada'] else 'Não'}</li>"
        resultado_html += "</ul>"

        # Aplicação de incisos
        resultado_html += "<h3>Aplicação de Incisos</h3><ul>"
        incisos_labels = ['Inciso I', 'Inciso II', 'Inciso III', 'Inciso IV', 'Inciso V', 'Inciso VI']
        for inciso, label in zip(resposta['aplicacao_incisos'], incisos_labels):
            resultado_html += f"<li>{label}: {'Sim' if inciso else 'Não'}</li>"
        resultado_html += "</ul>"
        """
        
        return resultado_html
    else:
        return "<p>Erro na análise da portaria.</p>"

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)

#if __name__ == '__main__':
#    app.run(debug=True)
    
    
