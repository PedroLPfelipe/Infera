# IMPORTAÇÃO DE BIBLIOTECAS
import json # Necessário para converter as triplas extraídas em formato JSON.
import streamlit as st # Interface Web.
import tempfile # Usado para criar arquivos temporários dos PDFs enviados.
import requests # Para chamadas HTTP (se necessário para APIs externas).
from rag_pipeline import RAGPipeline # Importação da classe RAGPipeline (lógica de processamento, vetorização e geração de respostas).
from graph_db import Neo4jClient # Importação do cliente para interação com o banco de dados Neo4j, onde o conhecimento extraído é armazenado como triplas.

# CONFIGURAÇÃO DA INTERFACE 
st.set_page_config(page_title="Graph RAG App", layout="wide") # Define o título da página e a largura do layout.
st.title("GraphRAG com Graphdatabase Neo4j") # Título principal da aplicação.

# Inicializa as variáveis de sessão
if 'vectorstore' not in st.session_state: # Importante para garantir que o vectorstore seja criado apenas uma vez por upload de PDF.
    st.session_state.vectorstore = None
if 'rag' not in st.session_state: # Permite que a instância do RAGPipeline seja mantida durante a sessão, evitando reprocessamentos desnecessários.
    st.session_state.rag = None

uploaded_file = st.file_uploader("Envie um arquivo PDF", type="pdf") # Limita o tipo de arquivo a ser enviado para PDF.

# PROCESSAMENTO INICIAL DO ARQUIVO
if uploaded_file and st.session_state.vectorstore is None: # Só processa o PDF se alguma coisa foi enviada e se o vectorstore ainda não foi criado.
    with st.spinner("Analisando..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp: # Cria um arquivo temporário para o PDF enviado, garantindo que ele seja salvo no sistema para processamento.
            tmp.write(uploaded_file.read())
            file_path = tmp.name

        st.session_state.rag = RAGPipeline() # Inicializa a pipeline RAG, que inclui a configuração dos modelos de linguagem e embeddings.
        docs = st.session_state.rag.load_pdf(file_path)
        st.session_state.vectorstore = st.session_state.rag.create_vectorstore(docs) # Cria o armazenamento vetorial a partir do documento processado.
        st.success("PDF processado e vetorizado.")

# SISTEMA MULTI-AGENTES (ABAS)
if st.session_state.vectorstore is not None:
    rag = st.session_state.rag
    # Permite que o usuário limpe os campos de entrada para consultas futuras.
    def limpar_param(): st.session_state.input_param = "" # Permite limpar a caixa de entrada da aba de parâmetros.
    def limpar_falha(): st.session_state.input_falha = "" # Permite limpar a caixa de entrada da aba de falhas/alarmes.

    # Duas abas especializadas: uma para parâmetros e outra para falhas/alarmes
    tab_param, tab_falhas = st.tabs([
        "⚙️ Parâmetros", 
        "🚨 Alarmes e Falhas"
    ])

    # ABA 1: ABA DE ANÁLISE FOCADA EM PARÂMETROS
    with tab_param: # Inicia a construção da aba de parâmetros.
        st.subheader("Consulta de Parâmetros") # Subtítulo da aba parâmetros.
        
        col_p1, col_p2 = st.columns([5, 1]) # Divide a aba em duas colunas, onde a primeira é para a entrada de texto e a segunda para o botão de limpar.
        with col_p1:
            query_p = st.text_input("Sua pergunta sobre parâmetros:", key="input_param")
        with col_p2:
            st.write("") ; st.write("")
            st.button("Limpar", key="btn_limpar_p", on_click=limpar_param, use_container_width=True) # Funciona como um refresh da caixa de entrada.
        
        if query_p: # Se o usuário digitou algo na caixa de entrada, inicia o processo de consulta.
            with st.spinner("Analisando parâmetro e atualizando grafo..."): # Mostra um spinner e uma mensagem de status enquanto o processamento está acontecendo.
                codigo = rag.extract_parameter_code(query_p)
                termo_busca = codigo if codigo != "Nenhum" else query_p # Termo de busca é o código extraído ou a própria pergunta se nenhum código for encontrado.
                st.caption(f"🔍 **Buscando no documento por:** `{termo_busca}`") # Exibe o termo que está sendo pesquisado no documento.
                
                docs_param = rag.retrieve(st.session_state.vectorstore, termo_busca) # Recupera os documentos relevantes do vectorstore usando o termo de busca como consulta.
                contexto_param = "\n".join([d.page_content for d in docs_param]) # Reúne o conteúdo dos documentos em um único contexto que será usado para gerar a resposta.
                
                resposta_p = rag.generate_parameter_answer(contexto_param, query_p) # A resposta sobre o parâmetro é gerada usando o contexto encontrado e a pergunta original.
                st.success(resposta_p) # Mostra a resposta gerada em um formato de sucesso (verde), indicando que tudo ocorreu bem.

                #  INTEGRAÇÃO NEO4J
                triples_p = rag.extract_triples(resposta_p) # As triplas são extraídas da resposta gerada.
                neo = Neo4jClient() # Inicializa o cliente do Neo4j para interação com o banco de dados.
                try: # Tenta converter as triplas extraídas para uma lista de dicionários (formato JSON) e inserir no grafo.
                    triplas_lista = json.loads(triples_p)
                    if triplas_lista:
                        neo.insert_triples(triplas_lista)
                        st.toast("Conhecimento do parâmetro salvo no grafo!")
                except Exception as e: # Se ocorrer algum erro, uma mensagem é mostrada para o usuário. 
                    st.error(f"Erro ao salvar no grafo: {e}") # Exibe qual foi o erro durante a inserção no grafo.
                finally:
                    neo.close() # Garante que a conexão com o banco de dados seja fechada, independentemente do sucesso ou falha da operação.
                                # O banco de dados é fechado independente do sucesso ou falha para evitar conexões abertas desnecessárias.

                with st.expander("Ver triplas extraídas (Conhecimento Técnico)"): # Cria um expander para mostrar as triplas extraídas em formato JSON.
                    st.code(triples_p, language="json")

    # ABA 2: ABA FOCADA NO DIAGNÓSTICO DE FALHAS E ALARMES
    with tab_falhas:
        st.subheader("Análise de Códigos de Falha e Alarme")
        
        col_f1, col_f2 = st.columns([5, 1])
        with col_f1:
            query_f = st.text_input("Sua pergunta sobre falhas/alarmes:", key="input_falha")
        with col_f2:
            st.write("") ; st.write("")
            st.button("Limpar", key="btn_limpar_f", on_click=limpar_falha, use_container_width=True)
        
        if query_f:
            with st.spinner("Diagnosticando falha e atualizando grafo..."):
                codigo_f = rag.extract_fault_code(query_f)
                termo_busca_f = codigo_f if codigo_f != "Nenhum" else query_f
                st.caption(f"🔍 **Buscando no documento por:** `{termo_busca_f}`")
                
                docs_falha = rag.retrieve(st.session_state.vectorstore, termo_busca_f)
                contexto_falha = "\n".join([d.page_content for d in docs_falha])
                
                resposta_f = rag.generate_fault_answer(contexto_falha, query_f)
                st.error(resposta_f) 

                # INTEGRAÇÃO NEO4J
                triples_f = rag.extract_triples(resposta_f)
                neo = Neo4jClient()
                try:
                    triplas_lista = json.loads(triples_f)
                    if triplas_lista:
                        neo.insert_triples(triplas_lista)
                        st.toast("Conhecimento da falha salvo no grafo!")
                except Exception as e:
                    st.error(f"Erro ao salvar no grafo: {e}")
                finally:
                    neo.close()

                with st.expander("Ver triplas extraídas (Conhecimento Técnico)"):
                    st.code(triples_f, language="json")
