from langchain.chat_models import init_chat_model
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os


new_vector_store = list()


def tipo_llm(llm="llama3-8b-8192"):
  return init_chat_model(llm, model_provider='groq')


def embed():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")



def processar_texto_gerar_embedding(uploaded_file):
    dict_documents = dict()
    
    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Processamento do PDF quando o arquivo é carregado
    if uploaded_file is not None:
        # Salva o arquivo temporariamente
        with open("uploaded_file.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Carrega e processa o PDF com PyPDFLoader
        loader = PyPDFLoader("uploaded_file.pdf")
        doc = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # chunk size (characters)
            chunk_overlap=200,  # chunk overlap (characters)
            add_start_index=True,  # track index in original document
        )
        
        all_splits = text_splitter.split_documents(doc)
        arquivo_nome = os.path.basename(all_splits[0].metadata['source']).replace('.pdf', '')
        dict_documents[arquivo_nome] = all_splits
            
            
        for nome, docs in dict_documents.items():
            vector_store = FAISS.from_documents(docs, embedding)
            vector_store.save_local(f"faiss_index_{0}")
            
            
        os.remove('uploaded_file.pdf')


def load_embedding():
    global new_vector_store 
    new_vector_store.clear()
    embeddings = embed()
    
    for i in range(123):
        new_vector_store.append(
            FAISS.load_local(
                f"minutas/faiss_index{i}", embeddings, allow_dangerous_deserialization=True
            )
        )
        
        
        
def load_one_embedding():
    global new_vector_store 
    new_vector_store.clear()
    try:
        embeddings = embed()
        
        new_vector_store.append(
            FAISS.load_local(
                f"faiss_index_0", embeddings, allow_dangerous_deserialization=True
            )
        )
    
    except:
        print('Talvez seja carregado apos fazer upload de documento')