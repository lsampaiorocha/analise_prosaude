# Sistema de robotização para captação de autos e análise de portaria da PROSAÚDE

## Descrição Geral
O sistema robotiza o recebimento de intimações no setor da PROSAÚDE, a captura dos arquivos contendo os autos dos processos a partir de sistemas externos, o armazenamento e a realização da análise inteligente destes autos, bem como a elaboração e realização dos despachos, levando em consideração o estabelecido na portaria 01/2017-PGE e as orientações do setor.

## Estrutura do Sistema
- `/app`: As rotas da API Flask e a lógica das ações das rotas.
- `/BD`: Script de criação das tabelas SQL.
- `/ModulosAnalise`: Arquivos da biblioteca de análise de documentos.
- `/arquivos`: Armazena arquivos dos autos completos processados (deve ser esvaziada regularmente).
- `/temp`: Arquivos temporários criados durante a análise.
- `/AnaliseAutos.py`: Biblioteca para analisar e extrair os documentos relevantes dos autos.
- `/AnalisePortaria.py`: Biblioteca para analisar e extrair todas as informações relevantes de um documento visando aplicação da portaria.
- `/RunServer.py`: Inicia a API como serviço.
- `/tabela_CMED.xls`: Tabela utilizada em algumas verificações relacionadas a medicamentos.


## Requisitos e Dependências
- **Python**: 3.11.7
- **Bibliotecas**:
  - `Flask`: Para a API
  - `SQLAlchemy`: Para interagir com o banco de dados
  - `LangChain`: Para as chamadas relacionadas ao uso de Large Language Models
  - `LangChain`: Para as chamadas relacionadas ao uso de Large Language Models
  - `requests`: Para integrações com APIs externas
  - Outros: Veja `requirements.txt`

