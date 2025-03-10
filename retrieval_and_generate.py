from langchain import hub
from langchain.prompts import PromptTemplate

from chatbot_process import load_embedding, load_one_embedding, tipo_llm, new_vector_store
import load_api
import os, re

def ativar_load_embeddings(boleano):
    if boleano == False:
        load_one_embedding()
        print('carregado somente 1 arquivo por vez')
    else:
        load_embedding()
        print('carregar aquivos pre salvos')

llm = tipo_llm()
# llm = tipo_llm('gemma2-9b-it')
# llm = tipo_llm('llama-3.3-70b-versatile')
# llm = tipo_llm('deepseek-r1-distill-llama-70b')

prompt = hub.pull("rlm/rag-prompt")

# Prepara o prompt
context = ''

# Prepara o resumo
resumo = ''


def processar_contexto(query):
    resultados_list = list()
    scores_list = list()

    global context
    global resumo
    
    for vs in new_vector_store:
        resultados = vs.similarity_search_with_score(query, k=4)
        
        score_atual = 0

        for res, score in resultados:
            if score > score_atual:
                resultados_list.append(res)
                scores_list.append(score)


    context = ''
    for i, (doc, score) in enumerate(zip(resultados_list, scores_list)):
        nome_doc = doc.metadata['source'].split('/')[-1]
        conteudo = doc.page_content

        context += f"Conteúdo: '{conteudo} Score: {score}'\n"
        
        
def processar_contexto_pre_carregado(query):
    resultados_list = list()
    
    global context
    global resumo
            
    for vs in new_vector_store:
        resultados = vs.similarity_search_with_score(query, k=3)

        for res, score in resultados:
            nome_arquivo = os.path.basename(res.metadata['source'])
            nome_empresa = nome_arquivo.split('_')
            
            if nome_empresa[-1].endswith('.pdf'):
                nome_empresa = nome_empresa[:-1]

            if nome_empresa[-1].isdigit():
                nome_empresa = nome_empresa[:-1]

                nome_empresa = ' '.join(nome_empresa)

                nome_empresa = ' '.join([part for part in nome_empresa.split() if len(part) > 4])

                pattern = r'\b(' + '|'.join(re.escape(part) for part in nome_empresa.split()) + r')\b'
                
                # Verifica se algum termo do nome da empresa aparece como palavra isolada na query
                if re.search(pattern, query, flags=re.IGNORECASE):
                    resultados_list.append((res, score))
                    print(nome_empresa)
        
    context = f""
    for i, doc in enumerate(resultados_list):
        score = doc[1]
        nome_doc = doc[0].metadata['source'].split('/')[-1]
        conteudo = doc[0].page_content
        context += f"Conteúdo: '{conteudo} Score: {score}'\n"


prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template='''{context}\n
A partir do contexto fornecido, retorne a resposta em português baseada na pergunta.

Priorize o documento que realmente responde à pergunta, mesmo que o score não seja o mais alto e que não tenha certeza sobre a resposta.

Devolva a resposta somente do documento mais relevante em relação a pergunta e o nome do documento recuperado.

No entanto, não forneça o documento retornado e algo relacionado a "o documento recuperado mais relevando é..." ao usuário,
apenas forneça a resposta que você pensou sobre o contexto atribuido

Pergunta: '{query}'.

'''
)


def processar_resposta(pergunta):
    prompt_llm = prompt_template.format(context=context, query=pergunta)
    
    try:
        resultado = llm.invoke(prompt_llm)
        return resultado.content.strip()
    
    except:
        return 'Reformule a pergunta, pois o meu limite foi excedido!'