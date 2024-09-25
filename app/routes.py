# app/routes.py
from flask import request, jsonify, Flask, render_template

from AnalisePortaria import *

def configure_routes(app):
  
  @app.route('/')
  def home():
      #return jsonify({"message": "Bem-vindo ao servidor!"})
      return render_template('upload.html')  

  @app.route('/analisePortaria', methods=['POST'])
  def analise():
        # Verifica se o arquivo foi enviado
        if 'pdf' not in request.files:
            return jsonify({"error": "Nenhum arquivo PDF enviado!"}), 400
        
        pdf_file = request.files['pdf']  # Obtém o arquivo PDF
        id_string = request.form.get('id')  # Obtém o ID

        # Adiciona depuração para ver o que o Flask está recebendo
        print(f"Arquivo recebido: {pdf_file.filename}, tamanho: {pdf_file.content_length} bytes")


        # Verifica se o arquivo tem nome e conteúdo
        if pdf_file.filename == '':
          return jsonify({"error": "Nenhum arquivo PDF selecionado!"}), 400

        # Verifica se o arquivo está vazio -- Causava Erro
        #if pdf_file.content_length == 0:
        #    #raise ValueError("O arquivo enviado está vazio!!")
        #  return jsonify({"error": "O arquivo enviado está vazio!"}), 400
        pdf_content = pdf_file.read()
        if len(pdf_content) == 0:
            return jsonify({"error": "O arquivo enviado está vazio!"}), 400
        pdf_file.seek(0)  # Reseta o ponteiro do arquivo



        if not id_string:
            return jsonify({"error": "ID não fornecido!"}), 400
        
        pdf_filename = f"{id_string}_{pdf_file.filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        pdf_file.save(file_path)

        
        
        models = {
          "honorarios" : "gpt-4o",
          "doutros" : "gpt-4o",
          "medicamentos" : "gpt-4o",
          "alimentares" : "gpt-4o",
          "internacao" : "gpt-4o",      
          "resumo" : "gpt-4o",
          "geral" : "gpt-4o"
        }
        
        
        # Aqui você pode processar o arquivo e o ID como quiser
        resultado = AnalisePortaria(pdf_file, models, pdf_filename, Verbose=True) 
        
        # Retorna a resposta com o resultado do processamento
        return jsonify(resultado), 200



