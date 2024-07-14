import streamlit as st
from FrontEnd.pagina_principal import *
import yaml
from yaml.loader import SafeLoader
from azure.storage.blob import BlobServiceClient
from streamlit_extras.add_vertical_space import add_vertical_space
from azure.storage.blob import BlobClient
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from streamlit_extras.stylable_container import stylable_container
from streamlit_extras.metric_cards import style_metric_cards
from datetime import datetime, timedelta
import stripe
from streamlit_oauth import OAuth2Component
import base64
import json
from streamlit_js_eval import streamlit_js_eval

# create an OAuth2Component instance
CLIENT_ID = st.secrets['CLIENT_ID']
CLIENT_SECRET = st.secrets['CLIENT_SECRET']
AUTHORIZE_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"


def sidebar_bg(side_bg):
    st.markdown(
        f"""
      <style>
      [data-testid="stSidebar"] > div:first-child {{
          background: url({side_bg});
          background-size: cover; /* Ajusta o tamanho da imagem para cobrir toda a área */
          background-position: center; /* Centraliza a imagem vertical e horizontalmente */
          background-repeat: no-repeat; /* Impede que a imagem seja repetida */
      }}
      </style>
      """,
        unsafe_allow_html=True,
    )


def controle_login():
    container_informacoes_pre_login = st.container()

    if "auth" not in st.session_state:
        # create a button to start the OAuth2 flow
        oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_ENDPOINT, TOKEN_ENDPOINT, TOKEN_ENDPOINT,
                                 REVOKE_ENDPOINT)

        st.sidebar.image('https://i.ibb.co/bsSqpHP/logo-com-nome.png', use_column_width=True)

        with st.sidebar:
            add_vertical_space(1)
            try:
                result = oauth2.authorize_button(
                    name="Entrar com Google",
                    icon="https://www.google.com.tw/favicon.ico",
                    #redirect_uri="https://ohmyroute.com",
                    #redirect_uri="http://localhost:8501",
                    redirect_uri="https://oh-my-route.streamlit.app",
                    scope="openid email profile",
                    key="google",
                    extras_params={"prompt": "consent", "access_type": "offline"},
                    use_container_width=True,
                    pkce='S256',
                )
            except:
                streamlit_js_eval(js_expressions="parent.window.location.reload()")

        if result:
            # st.write(result)
            # decode the id_token jwt and get the user's email address
            id_token = result["token"]["id_token"]
            # verify the signature is an optional step for security
            payload = id_token.split(".")[1]
            # add padding to the payload if needed
            payload += "=" * (-len(payload) % 4)
            payload = json.loads(base64.b64decode(payload))
            email = payload["email"]
            st.session_state["auth"] = email
            st.session_state["token"] = result["token"]
            st.rerun()

    if "auth" not in st.session_state:
        with container_informacoes_pre_login:
            sidebar_bg('https://i.ibb.co/5Wmk9Xp/lateraldosite.png')
            st.session_state.pagina_atual = 'pagina_principal'
            st.markdown(
                "<h1 style='text-align: center; font-size: 55px; font-weight: normal;'>Olá, seja bem-vindo!</h1>",
                unsafe_allow_html=True)

            add_vertical_space(1)
            st.image('https://i.ibb.co/nBJVhBB/bannersitenovo.png')

            add_vertical_space(1)
            st.markdown(
                "<h1 style='text-align: center; font-size: 36px; font-weight: normal;'>Melhore a Logística do seu Negócio <br> em 4 etapas!</h1>",
                unsafe_allow_html=True)
            add_vertical_space(1)
            col16, col17, col18, col30 = st.columns(4)
            with col16:
                st.image('https://i.ibb.co/9vW91Wm/caixa-1.png', use_column_width=True)

            with col17:
                st.image('https://i.ibb.co/1nfx2Mb/caixa2.png', use_column_width=True)

            with col18:
                st.image('https://i.ibb.co/4Fh1V0B/caixa3.png', use_column_width=True)

            with col30:
                st.image('https://i.ibb.co/jhzWQ7T/caixa4.png', use_column_width=True)

            add_vertical_space(3)
            col1, col2 = st.columns(2)
            with col1:
                video_url = "https://www.youtube.com/embed/HsGP7cqBNGU"  # Note: Use o link "embed" do YouTube
                st.video(video_url)

            with col2:
                st.markdown(
                    "<h1 style='text-align: center; font-size: 36px; font-weight: normal;'>O que é o Oh My Route?</h1>",
                    unsafe_allow_html=True)
                st.markdown(
                    "<h2 style='text-align: center; font-size: 27px; font-weight: normal;'><strong>Veja como funciona</strong></h2>",
                    unsafe_allow_html=True)
                st.markdown(
                    "<h2 style='text-align: center; font-size: 22px; font-weight: normal;'>É uma ferramenta online para "
                    "otimização de rotas, especialmente voltada para pequenas e médias empresas. <br>Com ela, "
                    "os usuários podem inserir diversos endereços e obter de imediato as rotas mais eficazes.</h2>",
                    unsafe_allow_html=True)

            add_vertical_space(2)
            col11, col12, col13 = st.columns([1, 3, 1])
            with col12:
                st.image('https://i.ibb.co/ZT1P8Bp/iconespeqenos.png', use_column_width=True)
            col51, col52, col53 = st.columns([1, 10, 1])
            with col52:
                st.markdown(
                    "<h2 style='text-align: center; font-size: 30px; font-weight: normal;'>A <strong>Oh My Route</strong> oferece o "
                    "otimizador de rotas mais abrangente e eficaz disponível, diminuindo seus gastos com logística!</h2>",
                    unsafe_allow_html=True)

            add_vertical_space(3)
            with stylable_container(
                    key="green_button",
                    css_styles="""
                        [data-testid="stVerticalBlock"] {
                            background-color: #0b2947;
                        }
                        """,
            ):
                with st.container():
                    col60, col61, col62, col63, col64 = st.columns([0.2, 0.7, 5, 1.2, 0.2])
                    with col61:
                        add_vertical_space(1)
                        st.image('https://i.ibb.co/jgZbbbk/perguntas-e-respostas.png', use_column_width=True)
                        add_vertical_space(1)
                    with col62:
                        add_vertical_space(1)
                        st.markdown(
                            "<h1 style='text-align: left; font-size: 25px; font-weight: normal;line-height: 0;'><strong>Possui alguma pergunta?</strong></h1>"
                            "<h1 style='text-align: left; font-size: 20px; font-weight: normal;line-height: 1;'>Contate-nos e saiba mais sobre como podemos parimorar sua logística</h1>",
                            unsafe_allow_html=True)
                    with col63:
                        email_address = "ohmyroute@gmail.com"
                        add_vertical_space(3)
                        with stylable_container(
                                key="green_button",
                                css_styles="""
                                    [data-testid="baseLinkButton-secondary"] {
                                        background-color: white;
                                        color: black;
                                        border-radius: 20px;
                                        width: 100%;
                                    }
                                    """,
                        ):
                            st.link_button("**Enviar E-mail**", f"mailto:{email_address}")


def pagina_instrucoes_de_uso():
    st.title('**Instruções de Uso**')

    st.header('Vídeo Demonstrativo', divider='blue')
    # Presumindo que você tenha um vídeo para inserir, use st.video('url_do_seu_vídeo')
    # st.write('Assista ao vídeo abaixo para uma rápida demonstração de como utilizar a ferramenta:')
    st.write('Em breve...')
    # Exemplo: st.video('https://www.linkdoseuvídeo.com')

    add_vertical_space(20)

    st.header('Informações Importantes', divider='blue')
    st.write("""
    - **Limite de Endereços**: Você pode calcular rotas para até 100 endereços por vez.
    - **Consumo de Créditos**: Cada cálculo de rota consome um crédito por entrega.
    - **Créditos Iniciais**: Novos usuários recebem 30 créditos gratuitos para testar a ferramenta.
    - **Adicionar Créditos**: Para comprar mais créditos, acesse a página "Adicionar Créditos".
    - **Validade dos Créditos**: Todos os créditos adquiridos têm validade de 90 dias. Importante: a validade de todos os seus créditos é resetada a cada nova aquisição, estendendo o período de uso por mais 90 dias a partir dessa data.
    - **Precisão de Endereços**: Para garantir a melhor experiência, insira os endereços com a máxima precisão. A ferramenta não se responsabiliza por endereços não encontrados.
    """)

    st.header('Como Calcular uma Rota', divider='blue')
    st.write("""
    Siga os passos abaixo para calcular sua rota de entregas de forma eficiente:

    1. **Acessar a Página de Cálculo de Rotas**: Navegue até a página dedicada ao cálculo de rotas.
    2. **Endereço de Partida**: Informe o endereço de partida para suas entregas.
    3. **Número de Entregadores/Viagens**: Defina quantos entregadores estão disponíveis ou quantas viagens deseja realizar.
    4. **Limite de Carga**: Estabeleça um limite de carga para o veículo, que pode ser em peso ou volume. Mantenha sempre a mesma unidade de medida para consistência.
    5. **Modelo de Otimização**: Escolha entre o modelo de otimização de carga, que distribui de forma ótima a carga entre os entregadores, e o modelo de entregas, que divide as entregas de maneira equilibrada, independente da carga.
    6. **Planilha de Endereços**: Faça o download do modelo de planilha fornecido, preencha com os endereços de entrega conforme as instruções e faça o upload no sistema.
    7. **Confirmação e Cálculo**: Verifique as informações inseridas e prossiga com o cálculo das rotas.
    8. **Download e Mapa Interativo**: Após o cálculo, faça o download das rotas e utilize o mapa interativo para visualizar a sequência das entregas e confirmar a precisão dos endereços.

    Seguindo estes passos, você maximizará a eficiência das suas entregas e garantirá a melhor utilização dos seus recursos.
    """)


def atualizar_creditos_usuario():
    username = st.session_state["auth"]

    try:
        creditos, data_ultima_compra_str = consultar_usuario(username)
    except:
        adicionar_ou_atualizar_usuario(username, 30, datetime.now().strftime('%Y-%m-%d'))
        creditos, data_ultima_compra_str = consultar_usuario(username)

    data_ultima_compra = datetime.strptime(data_ultima_compra_str, '%Y-%m-%d')

    diferenca_dias = (datetime.now() - data_ultima_compra).days

    if diferenca_dias >= 91:
        adicionar_ou_atualizar_usuario(username, 0, data_ultima_compra_str)
        return consultar_usuario(username)[0], '----'
    else:
        data_ultima_compra = datetime.strptime(data_ultima_compra_str, '%Y-%m-%d')
        data_ultima_compra_mais_90_dias = data_ultima_compra + timedelta(days=90)
        data_ultima_compra_mais_90_dias_str = data_ultima_compra_mais_90_dias.strftime('%Y-%m-%d')
        if creditos > 0:
            return creditos, data_ultima_compra_mais_90_dias_str[-2:] + '/' + data_ultima_compra_mais_90_dias_str[-5:-3]
        else:
            return creditos, '----'


def pagina_compra_creditos():
    stripe.api_key = st.secrets['STRIPE']

    st.markdown(
        "<h1 style='text-align: center; font-size: 55px; font-weight: normal;'>Suas entregas podem ir mais longe</h1>",
        unsafe_allow_html=True)

    st.markdown(
        "<h1 style='text-align: center; font-size: 38px; font-weight: normal;'>Adiquira mais créditos</h1>",
        unsafe_allow_html=True)

    add_vertical_space(1)
    col1, col4, col2, col5, col3 = st.columns([20, 1, 20, 1, 20])

    with col1:
        col9, col10, col11 = st.columns([1, 10, 1])
        col10.image('https://i.ibb.co/PFk1Mxs/Bronze.png', use_column_width=True)
        with stylable_container(
                key="green_button_30",
                css_styles="""
                    a[data-testid="baseLinkButton-secondary"] {
                        width: 100%;
                        background-color: #016bce;
                    }
                    """,
        ):
            st.link_button("**Comprar**", "https://buy.stripe.com/6oE6pxeh2gDn84UeUU")

    with col2:
        col6, col7, col8 = st.columns([1, 10, 1])
        col7.image('https://i.ibb.co/r44t2DN/prata.png', use_column_width=True)
        with stylable_container(
                key="green_button_140",
                css_styles="""
                            a[data-testid="baseLinkButton-secondary"] {
                                width: 100%;
                                background-color: #016bce;
                            }
                            """,
        ):
            st.link_button("**Comprar**", "https://buy.stripe.com/aEU29heh2drb2KA5kl")

    with col3:
        col12, col13, col14 = st.columns([1, 10, 1])
        col13.image('https://i.ibb.co/qjbjW88/Ouro.png', use_column_width=True)
        with stylable_container(
                key="green_button_280",
                css_styles="""
                            a[data-testid="baseLinkButton-secondary"] {
                                width: 100%;
                                background-color: #016bce;
                            }
                            """,
        ):
            st.link_button("**Comprar**", "https://buy.stripe.com/cN2019fl60Epad26oq")

    st.subheader("", divider='blue')
    st.markdown("""
    **Nota:** Os créditos são válidos por **90 dias** a partir da data de compra. Além disso, ao adquirir mais créditos, a validade dos créditos que você já possui é extendida para os próximos 90 dias também.
    """, unsafe_allow_html=True)

    add_vertical_space(3)
    with stylable_container(
            key="green_button",
            css_styles="""
                            [data-testid="stVerticalBlock"] {
                                background-color: #0b2947;
                            }
                            """,
    ):
        with st.container():
            col60, col61, col62, col63, col64 = st.columns([0.2, 0.7, 5, 1.2, 0.2])
            with col61:
                add_vertical_space(1)
                st.image('https://i.ibb.co/jgZbbbk/perguntas-e-respostas.png', use_column_width=True)
                add_vertical_space(1)
            with col62:
                add_vertical_space(1)
                st.markdown(
                    "<h1 style='text-align: left; font-size: 25px; font-weight: normal;line-height: 0;'><strong>Possui alguma pergunta?</strong></h1>"
                    "<h1 style='text-align: left; font-size: 20px; font-weight: normal;line-height: 1;'>Contate-nos e saiba mais sobre como podemos parimorar sua logística</h1>",
                    unsafe_allow_html=True)
            with col63:
                email_address = "ohmyroute@gmail.com"
                add_vertical_space(3)
                with stylable_container(
                        key="green_button",
                        css_styles="""
                                        [data-testid="baseLinkButton-secondary"] {
                                            background-color: white;
                                            color: black;
                                            border-radius: 20px;
                                            width: 100%;
                                        }
                                        """,
                ):
                    st.link_button("**Enviar E-mail**", f"mailto:{email_address}")



def seletor_paginas():
    if 'pagina_atual' not in st.session_state:
        st.session_state.pagina_atual = 'pagina_principal'

    st.sidebar.image('BackEnd/imagens/logo com nome.png', use_column_width=True)
    st.sidebar.subheader('', divider='blue')
    with st.sidebar:
        with stylable_container(
                key="green_button",
                css_styles="""
                    button {
                        width: 100%;
                    }
                    """,
        ):
            add_vertical_space(1)
            if st.button("Calculo de rotas"):
                st.session_state.pagina_atual = 'pagina_principal'
            if st.button("Adicionar créditos"):
                st.session_state.pagina_atual = 'compra_creditos'
            if st.button("Intruções de uso"):
                st.session_state.pagina_atual = 'instrucoes_de_uso'
            if st.button("Sair"):
                del st.session_state["auth"]
                del st.session_state["token"]
                st.rerun()

        add_vertical_space(1)
        st.header('Créditos', divider='blue')
        add_vertical_space(1)
        creditos, validade = atualizar_creditos_usuario()
        col1, col2 = st.columns(2)
        col1.metric(label="Quantidade", value=creditos)
        col2.metric(label="Validos até", value=validade)
        style_metric_cards(border_left_color='#007bff', background_color='#2B2B3B', border_color='#2B2B3B')

    if st.session_state.pagina_atual == 'pagina_principal':
        pagina_principal()
    elif st.session_state.pagina_atual == 'instrucoes_de_uso':
        pagina_instrucoes_de_uso()
    elif st.session_state.pagina_atual == 'compra_creditos':
        pagina_compra_creditos()


def app():
    st.set_page_config(layout='wide', page_title='Oh My Route', page_icon='https://i.ibb.co/pf2spMy/Layer-4a.png',
                       initial_sidebar_state='expanded')

    controle_login()

    if "auth" in st.session_state:
        seletor_paginas()
