#!/usr/bin/env bash

python3 -m venv env

cp -r env_example .env

venv_folder="env/bin/python"

install_packages() {
    "$venv_folder" -m pip install --upgrade pip
    "$venv_folder" -m pip install "$@"
}

# Chamando a função com os pacotes desejados
install_packages streamlit pypdf python-dotenv
install_packages langchain[groq] langchain-huggingface langchain langchain-community faiss-cpu langchain_core langgraph