# app/routes.py
from flask import request, jsonify, Flask, render_template
from AnalisePortaria import *

#Lógica de execução das rotas
from .logica import *

#JC
from urllib.parse import unquote


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
    return importar_processos()
  

  @app.route('/AnalisarProcessosMarcados', methods=['POST'])
  def analise_marcados():
    
    """
    Rota para analisar e gerar o despacho de todos os processos da tabela tb_analiseportaria tais que:
        - não tenham sido ainda analisados
        - estejam marcados para análise 
        - possuam o campo id_documento definido
    """ 
    
    return analisar_marcados()

      

