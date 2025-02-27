# Rag_prospect

```
├── data/                 # Documentos e dados de entrada
│   └── documentos.csv
│
├── embeddings/           # Scripts para gerar e armazenar embeddings
│   └── create_embeddings.py
│
├── retrieval/            # Código para a recuperação de documentos
│   └── retriever.py
│
├── chains/               # Configuração das chains (integração de retrieval e geração)
│   └── rag_chain.py
│
├── monitoring/           # Integração com Langsmith para logging e métricas
│   └── langsmith_integration.py
│
└── app.py                # Aplicação principal em Streamlit

```
