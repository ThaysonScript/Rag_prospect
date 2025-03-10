import time
import streamlit as st

from chatbot_process import processar_texto_gerar_embedding
from retrieval_and_generate import ativar_load_embeddings, processar_contexto, processar_contexto_pre_carregado, processar_resposta

st.set_page_config(page_title='B3 - AI Prospects Analysis', page_icon=':moneybag:', layout='wide')
st.title(':moneybag: B3 - AI Prospects Analysis')


ativar = st.checkbox('ativar')
ativar_load_embeddings(ativar)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    
    
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
 

def save_feedback(index):
    st.session_state.history[index]["feedback"] = st.session_state[f"feedback_{index}"]


if "history" not in st.session_state:
    st.session_state.history = []


for i, message in enumerate(st.session_state.history):
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["role"] == "assistant":
            feedback = message.get("feedback", None)
            st.session_state[f"feedback_{i}"] = feedback
            st.feedback(
                "thumbs",
                key=f"feedback_{i}",
                disabled=feedback is not None,
                on_change=save_feedback,
                args=[i],
            )
    
    
def ativar_recuperador(prompt):
    if not ativar:
        processar_contexto(prompt)
    else:
        processar_contexto_pre_carregado(prompt)
    
def chat_stream(prompt):
    ativar_recuperador(prompt)
    
    response = f'Você perguntou... "{prompt}".\n\n{processar_resposta(prompt)}'

    for char in response:
        yield char
        time.sleep(.001)
 
           
def system_chat_message(prompt):
    with st.chat_message("assistant"):
        response = st.write_stream(chat_stream(prompt))
        st.feedback(
            "thumbs",
            key=f"feedback_{len(st.session_state.history)}",
            on_change=save_feedback,
            args=[len(st.session_state.history)],
        )
    
    st.session_state.history.append({"role": "assistant", "content": response})
    
        
def human_chat_message():
    if prompt := st.chat_input("Pergunte alguma coisa para o assistente"):
        with st.chat_message("user"):
            st.write(prompt)
         
        st.session_state.history.append({"role": "user", "content": prompt})
        system_chat_message(prompt)


def chat_input():
    human_chat_message()    
    
    if st.button('limpar historico'):
        st.session_state.messages = []
        st.session_state.history = []


chat_input()

# Interface para fazer o upload do arquivo
uploaded_file = st.file_uploader("Faça o upload de um arquivo PDF", type="pdf")

if uploaded_file is not None:
    if "uploaded_file" not in st.session_state or st.session_state.uploaded_file != uploaded_file.name:
        st.session_state.uploaded_file = uploaded_file.name
        processar_texto_gerar_embedding(uploaded_file)
        st.success("Arquivo processado com sucesso!")