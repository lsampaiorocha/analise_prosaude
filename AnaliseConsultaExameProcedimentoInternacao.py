from langchain_core.prompts import PromptTemplate

#organizar outputs
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

# Define your desired data structure.
class Inter(BaseModel):
    inter: list[str] = Field(description="Lista de itens que são consultas, exames, procedimentos clínicos e cirúrgicos")


#Recebe uma retrieval chain de uma sentença e retorna uma lista de intervenções
# pares (medicamento, dosagem_em_mg)
def AnaliseConsultaExameProcedimentoInternacao(chain, llm, Verbose=False):
    #Aqui o objetivo  dos prompts  é listar os itens que não são medicamentos (não está funcionando bem)
    
    q1 = """
        Você é um assessor jurídico analisando um documento que contém uma decisão judicial.
        
        Você deve limitar sua análise ao trecho da sentença, onde ele declara que julga procedente ou improcedente o pedido.
        
        Considere uma consulta médica como uma interação entre um paciente e um profissional de saúde, tipicamente um médico, para avaliação, diagnóstico e planejamento do tratamento de qualquer condição de saúde. 
        
        Considere como um exames médico um procedimento laboratorial ou de imagem que ajude a avaliar e diagnosticar problemas de saúde do paciente.
        
        Considere como procedimento clínicos ou cirúrgico uma intervenção terapêuticas para tratar doenças, lesões ou deformidades.
        
        Sua tarefar é identificar e extrair qualquer menção à realização de consultas, exames, e procedimentos clínicos e cirúrgicos na sentença.
        
        Sua resposta deve ser uma lista contendo os itens extraídos da sentença.
    """
    
    r1 = chain.invoke({"input": q1}).get('answer')  
    
    parser = JsonOutputParser(pydantic_object=Inter)

    prompt = PromptTemplate(
        template="Forneça apenas a lista com os nomes dos itens que não são medicamentos.\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain3 = prompt | llm | parser

    lo = chain3.invoke({"query": r1}).get("outr") 
        
    return lo
