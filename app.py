from flask import Flask, request, jsonify, render_template
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


# Configuração da chave da API GPT
env_path = os.path.join(base_directory, 'ambiente.env')
load_dotenv(env_path)  # Carrega as variáveis de ambiente de .env

api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    raise RuntimeError("OPENAI_API_KEY não está definida")


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        incisos = request.form.getlist('incisos')
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            #comentado para utilizar os arquivos que já estão na pasta de upload para ficar mais rápido
            #file.save(filepath)
            resposta = analisar_portaria(filepath, incisos)  # Função que analisa o arquivo usando LLMs
            return jsonify(resposta=resposta)
        else:
            return jsonify(resposta="Nenhum arquivo enviado.")
    else:
        return render_template('upload.html')



if __name__ == '__main__':
    app.run(debug=True)
    
