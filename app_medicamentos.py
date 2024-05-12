from flask import Flask, request, jsonify, render_template
#from werkzeug.utils import secure_filename
import os

#importa as funções de análise
from analise_portaria import *


# Define o caminho base como o diretório atual onde o script está sendo executado
base_directory = os.getcwd()

# Configura o diretório de templates e uploads usando caminhos relativos

# Configuração inicial do Flask
app_medicamentos = Flask(__name__, template_folder=os.path.join(base_directory, 'templates'))
#app.config['UPLOAD_FOLDER'] = os.path.join(base_directory, 'uploads')


# Configuração da chave da API GPT
#env_path = os.path.join(base_directory, 'ambiente.env')
#load_dotenv(env_path)  # Carrega as variáveis de ambiente de .env

#api_key = os.environ.get('OPENAI_API_KEY')
#if not api_key:
#    raise RuntimeError("OPENAI_API_KEY não está definida")


@app_medicamentos.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        meds = request.form.get('medications')
        if meds:
            resposta = analisar_medicamentos(meds)  # Função que analisa os medicamentos
            return jsonify(resposta=resposta)
        else:
            return jsonify(resposta="Medicamentos não foram preenchidos.")
    else:
        return render_template('medicamentos.html')



if __name__ == '__main__':
    app_medicamentos.run(debug=True, port=5001)
    
