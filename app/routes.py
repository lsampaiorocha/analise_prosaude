# app/routes.py
from flask import request, jsonify, Flask, render_template
from AnalisePortaria import *

#Lógica de execução das rotas
from .logica import *


def configure_routes(app):
  
  @app.route('/')
  def home():
    return render_template('upload.html')

    
  @app.route('/ImportarProcessos', methods=['POST'])
  def importacao_processos():
    
    """
    Rota para importar os processos de intimações cujos autos já tenham sido baixados pelos
    robô de distribuição de processos (tabela tb_autosprocessos) para a tabela tb_analiseportaria
    """ 
    importar_processos()
  

  @app.route('/AnalisarProcessosMarcados', methods=['POST'])
  def analise_marcados():
    
    """
    Rota para analisar todos os processos da tabela tb_analiseportaria tais que:
        - não tenham sido ainda analisados
        - estejam marcados para análise 
        - possuam o campo id_documento definido
    """ 
    
    analisar_marcados()

    
    
    
  @app.route('/AnalisePortariaProcesso', methods=['POST'])
  def analise_processo():
        """
        Rota de análise de aplicação de portaria para um processo.
        A rota recebe um número de processo como parâmetro e executa diversas etapas necessárias para
        análise, desde a recuperação dos autos no Alfresco, até a extração do documento a ser analisado
        e aplicação do pipeline de análise de aplicação de portaria
        
        Parâmetros:
        - numero_processo (form): Número do processo a ser analisado.
        
        Fluxo:
        1. Validação do número de processo e mesmo foi marcado para análise.
        2. Download dos autos completos do processo (Alfresco).
        3. Processamento dos autos para extrair o documento a ser analisado
        4. Execução do pipeline de Análise.
        5. Escrita dos resultados da análise no BD.
        """    
        
        numero_processo = request.form.get('numero_processo')
        #TODO: Verificar casos em que o número não tenha sido passado no formato padrão
        
        analisar_processo(numero_processo)

    
  @app.route('/CapturaIdsProcessos', methods=['POST'])
  def Captura_ids():
    '''
    Função que baixa os autos a partir de um número de processo e preenche a tabela tb_documentosautos.
    '''
    numero_processo = request.form.get('numero_processo')
    retorno = captura_ids_processo(numero_processo)    
    if retorno is True:
      return jsonify({"message": "Processo atualizado com sucesso."}), 200
      