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
    return "Serviço disponível - v1.4.0"
  
  #habilita o funcionamento do robô
  @app.route('/HabilitarRobo', methods=['POST'])
  def habilitar():
    
    ligar_desligar(flag=True)
    
    return "Robô Habilitado"
  
  
  #desabilita o funcionamento do robô
  @app.route('/DesabilitarRobo', methods=['POST'])
  def desabilitar():
    
    ligar_desligar(flag=False)
    
    return "Robô Desabilitado"

  #importar os processos recebidos e cujos autos já foram coletados caso o robô esteja ligado
  @app.route('/ImportarProcessos', methods=['POST'])
  def importacao_processos():
    
    """
    Rota para importar os processos de intimações cujos autos já tenham sido baixados pelos
    robô de distribuição de processos (tabela tb_autosprocessos) para a tabela tb_analiseportaria
    """ 
    
    flag = obter_status_robo()
    
    if flag:
      return importar_processos()
    else:
      return "Não foi possível importar os processos, o robô está desabilitado"
  
  #analisar os processos que estão marcados para análise caso o robô esteja ligado
  @app.route('/AnalisarProcessosMarcados', methods=['POST'])
  def analise_marcados():
    
    """
    Rota para analisar e gerar o despacho de todos os processos da tabela tb_analiseportaria tais que:
        - não tenham sido ainda analisados
        - estejam marcados para análise 
        - possuam o campo id_documento definido
    """ 
    
    flag = obter_status_robo()
    
    if flag:
      return analisar_marcados()
    else:
      return "Não foi possível analisar os processos, o robô está desabilitado"
    
    
    

#importar os processos recebidos e cujos autos já foram coletados independente do robô estar ligado
  @app.route('/ImportarProcessosOff', methods=['POST'])
  def importacao_processos_off():
    
    """
    Rota para importar os processos de intimações cujos autos já tenham sido baixados pelos
    robô de distribuição de processos (tabela tb_autosprocessos) para a tabela tb_analiseportaria
    """ 
    print("Importação Offline")
    
    return importar_processos()
    
    
#analisar os processos que estão marcados para análise independente do robô estar ligado
  @app.route('/AnalisarProcessosMarcadosOff', methods=['POST'])
  def analise_marcados_off():
    
    """
    Rota para analisar e gerar o despacho de todos os processos da tabela tb_analiseportaria tais que:
        - não tenham sido ainda analisados
        - estejam marcados para análise 
        - possuam o campo id_documento definido
    """ 
    
    return analisar_marcados()  

