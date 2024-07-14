import streamlit as st
from BackEnd.calculo_de_rotas import *
from streamlit_extras.add_vertical_space import add_vertical_space
import base64
import zipfile
import shutil
from io import BytesIO
import pydeck as pdk
from datetime import datetime
from azure.cosmosdb.table.tableservice import TableService
from azure.cosmosdb.table.models import Entity

API_KEY = st.secrets['API_KEY']


def consultar_usuario(username):
    connection_string = st.secrets['COSMODB']
    table_service = TableService(connection_string=connection_string)

    users = table_service.query_entities("CreditosUsuario", filter="PartitionKey eq '{}'".format(username))

    for user in users:
        return user.Creditos, user.DataUltimaCompra


# Adicionar ou atualizar uma entidade na tabela
def adicionar_ou_atualizar_usuario(username, creditos, data_ultima_compra):
    connection_string = st.secrets['COSMODB']
    table_service = TableService(connection_string=connection_string)
    user = Entity()
    user.PartitionKey = username
    user.RowKey = username  # Para a API de Tabela, cada entidade é identificada unicamente pelo seu PartitionKey e RowKey
    user.Creditos = creditos
    user.DataUltimaCompra = data_ultima_compra

    table_service.insert_or_replace_entity("CreditosUsuario", user)


def get_binary_file_downloader_html(file_path, file_label='File', filename='output.xlsx'):
    with open(file_path, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{filename}">{file_label}</a>'
    return href


@st.cache_data
def validar_endereco_inicio(endereco_partida):
    try:
        coordenadas = obter_coordenadas(endereco_partida, API_KEY)
    except:
        return None

    if coordenadas is None:
        return None
    else:
        return [coordenadas['lat'], coordenadas['lng']]


@st.cache_data
def importar_planilha_entregas(df):
    return pd.read_excel(df, dtype={'Code': str, 'Address': str}, skiprows=1)


@st.cache_data
def teste_planilha(df, limite_carga):
    required_columns = ['Code', 'Address', 'Load']

    if not all(col in df.columns for col in required_columns):
        return 'Column names differ from template'

    df.rename(columns={'Code': 'Código', 'Address': 'Endereço', 'Load': 'Carga'}, inplace=True)

    try:
        df['Carga'] = pd.to_numeric(df['Carga'], errors='raise')
    except ValueError:
        return 'The data in the Load column is not all numeric'

    if df['Código'].duplicated().any():
        return 'There are duplicate codes in the spreadsheet'

    if len(df['Carga']) > 100:
        return 'Number of deliveries exceeds the limit of 100 deliveries at a time'

    if df.isnull().any().any():
        return 'There are missing values in the spreadsheet'

    if df['Carga'].min() <= 0:
        return 'There are deliveries with a load less than zero'

    if df['Carga'].max() > limite_carga:
        return 'There are deliveries with a higher load than the established limit'

    return 'Success'


def descobrir_coordenadas(df):
    try:
        df[['Latitude', 'Longitude']] = df.apply(aplicar_obter_coordenadas, chave_api=API_KEY, axis=1)
    except:
        return None

    return df


def checar_se_algum_endereco_nao_foi_obtido(df):
    codigos_sem_endereco = df[df['Latitude'].isnull()]

    if not codigos_sem_endereco.empty:
        st.warning('Some addresses were not obtained:')
        st.table(codigos_sem_endereco)
        return False
    return True


def limpar_diretorio(diretorio):
    # Verifica se o diretório existe
    if not os.path.exists(diretorio):
        # O diretório não existe; optou-se por criar o diretório
        os.makedirs(diretorio, exist_ok=True)
        return  # Sai da função pois o diretório estava vazio (acabou de ser criado)

    # O diretório existe, prossegue com a limpeza
    for filename in os.listdir(diretorio):
        file_path = os.path.join(diretorio, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            st.error(f'Falha ao deletar {file_path}. Razão: {e}')


@st.cache_data(ttl='1d')
def calcular_rotas(df_enderecos, numero_entregadores, limite_de_carga, tipo_otimizacao, ponto_partida, endereco_origem, diretorio):
    df_entregas_otimizadas = otimizar_entregas(df_enderecos, numero_entregadores, limite_de_carga, tipo_otimizacao)
    rotas_por_cluster = resolver_tsp_por_cluster(df_entregas_otimizadas, ponto_partida)
    temp_dist = calcular_tempo_distancia_por_rota(rotas_por_cluster, endereco_origem, df_entregas_otimizadas)
    df_final = construir_df_final(rotas_por_cluster, df_entregas_otimizadas, temp_dist, ponto_partida)
    return df_final


def disponibilizar_download_pasta_como_zip(pasta_path, col8, nome_arquivo_zip='arquivos.zip'):
    # Criar um arquivo ZIP na memória
    memoria_zip = BytesIO()
    with zipfile.ZipFile(memoria_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(pasta_path):
            for file in files:
                # Cria um caminho relativo para os arquivos para evitar a inclusão da estrutura de pastas completa
                file_path = os.path.join(root, file)
                zipf.write(file_path, arcname=os.path.relpath(file_path, start=pasta_path))

    # Volta ao início do arquivo na memória para permitir sua leitura
    memoria_zip.seek(0)

    # Criar botão de download no Streamlit
    col8.header('Download PDFs with routes', divider='blue')
    col8.download_button(
        label="Download files",
        data=memoria_zip,
        file_name=nome_arquivo_zip,
        mime="application/zip"
    )


def plot_map(df, cluster_selecionado, tamanho_ponto):
    df_filtrado = df[df['Cluster'] == cluster_selecionado]

    # Certifique-se de que as coordenadas estão na ordem correta [latitude, longitude]
    data = [{
        "position": [coords[1], coords[0]],  # Inverte a ordem aqui se necessário
        "tooltip": "Departure Location" if idx == 0 else f"Stops {idx}"
    } for idx, coords in enumerate(df_filtrado['coordenadas'].iloc[0])]

    view_state = pdk.ViewState(
        latitude=df_filtrado['coordenadas'].iloc[0][0][0],  # Certifique-se de que este é latitude
        longitude=df_filtrado['coordenadas'].iloc[0][0][1],  # Certifique-se de que este é longitude
        zoom=12,  # Ajuste o zoom conforme necessário para melhor visualização
        pitch=0)

    layer = pdk.Layer(
        type='ScatterplotLayer',
        data=data,
        get_position='position',
        get_color='[0, 0, 255, 160]',  # Cor dos pontos em RGBA: Azul
        get_radius=tamanho_ponto,  # Usa o valor do slider para definir o tamanho dos pontos
        get_elevation=30,
        elevation_scale=40,
        pickable=True,
    )

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/dark-v9',
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{tooltip}"}
    ))


def pagina_principal():
    st.title('ROUTE CALCULATION')

    # Endereço de partida
    st.header('Departure address', divider='blue')
    col1, col2, col3 = st.columns([3, 1, 3])
    coordenadas_partida = None
    with col2:
        add_vertical_space(2)
    endereco_partida = col1.text_input('Enter the starting address:')
    if col2.button('Validate'):
        if endereco_partida:
            coordenadas_partida = validar_endereco_inicio(endereco_partida)
            with col3:
                add_vertical_space(1)
                if coordenadas_partida is None:
                    st.error('Address not found')
    if coordenadas_partida:
        with col3:
            add_vertical_space(1)
            st.success('Validated address')

    # Parametros da simulação
    add_vertical_space(2)
    st.header('Parameter definition', divider='blue')
    col4, col5, col6 = st.columns(3)
    with col4:
        st.subheader('Deliverers')
        numero_de_entregadores = st.number_input('Number of couriers', step=1, key='numero_de_entregadores', value=1)
        if numero_de_entregadores <= 0:
            st.error('invalid value')
    with col5:
        st.subheader('Maximum load')
        carga_maxima_veiculos = st.number_input('Limite de carga dos veiculos', step=1, key='maxima_veiculos', value=1)
        if carga_maxima_veiculos <= 0:
            st.error('invalid value')
    with col6:
        st.subheader('optimizer')
        otimizador = st.selectbox("Type of optimization", ["Load", "deliveries"], key='otimizador')
        if otimizador == 'Load':
            otimizador = 'carga'

    # Planilha de cadastro de entregas
    add_vertical_space(2)
    st.header('Send a delivery schedule', divider='blue')

    col10, col11 = st.columns(2)
    my_file_path = "BackEnd/Delivery registration templete.xlsx"
    col11.markdown(f'<div style="font-size: {20}px">{"Download template spreadsheet"}</div>', unsafe_allow_html=True)
    col11.markdown(get_binary_file_downloader_html(my_file_path, 'Click here', 'Delivery registration templete.xlsx'), unsafe_allow_html=True)
    planilha_de_entregada = col10.file_uploader('Upload the delivery sheet', accept_multiple_files=False, label_visibility='collapsed')
    if planilha_de_entregada:
        df_entregas = importar_planilha_entregas(planilha_de_entregada)
        status_planilha = teste_planilha(df_entregas, carga_maxima_veiculos)
        if status_planilha == 'Success':
            with st.expander('View spreadsheet'):
                st.table(df_entregas.rename(columns={'Código': 'Code', 'Endereço': 'Address', 'Carga': 'Load'}))
            df_entregas.rename(columns={'Code': 'Código', 'Address': 'Endereço', 'Load': 'Carga'}, inplace=True)
            df_entregas = descobrir_coordenadas(df_entregas)
            if df_entregas is None:
                st.error('Error obtaining address coordinates')
            else:
                if checar_se_algum_endereco_nao_foi_obtido(df_entregas):
                    diretorio = f'BackEnd/pastas_de_rotas/{st.session_state["auth"]}'
                    add_vertical_space(2)
                    col7, col8 = st.columns(2)
                    placeholder_slider = st.empty()
                    placeholder_selectbox = st.empty()
                    col7.header('Calculating routes', divider='blue')

                    if 'df_final_rotas' not in st.session_state:
                        st.session_state.df_final_rotas = None

                    if (col7.button('Calculate routes')) & (len(df_entregas['Carga']) <= consultar_usuario(st.session_state["auth"])[0]):
                        limpar_diretorio(diretorio)
                        df_final = calcular_rotas(df_entregas, numero_de_entregadores, carga_maxima_veiculos, otimizador, validar_endereco_inicio(endereco_partida), endereco_partida, diretorio)
                        st.session_state.df_final_rotas = df_final
                        gerar_pdf_para_cluster(df_final, diretorio, 'en')
                        adicionar_ou_atualizar_usuario(st.session_state["auth"], consultar_usuario(st.session_state["auth"])[0] - len(df_entregas['Carga']), consultar_usuario(st.session_state["auth"])[1])
                    else:
                        if len(df_entregas['Carga']) > consultar_usuario(st.session_state["auth"])[0]:
                            col7.error('You don\'t have enough credits to calculate routes')

                    if st.session_state.df_final_rotas is not None:
                        # Sempre renderiza os widgets nos placeholders definidos
                        tamanho_ponto = placeholder_slider.slider('Dot size', min_value=50, max_value=1000,
                                                                  value=50, step=50, key='tamanho_ponto')
                        cluster_selecionado = placeholder_selectbox.selectbox('Select a route',
                                                                              st.session_state.df_final_rotas[
                                                                                  'Cluster'].unique(),
                                                                              key='cluster_selecionado')

                        # Chama a função de plotagem com os valores atualizados
                        plot_map(st.session_state.df_final_rotas, cluster_selecionado, tamanho_ponto)

                    if os.path.exists(diretorio) or os.path.isdir(diretorio):
                        disponibilizar_download_pasta_como_zip(diretorio, col8)

        else:
            st.error(status_planilha)
