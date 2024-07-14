import streamlit as st
from FrontEnd.pagina_principal_en import *
import streamlit_authenticator as stauth
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
from streamlit_extras.stylable_container import stylable_container
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
                    name="Login with Google",
                    icon="https://www.google.com.tw/favicon.ico",
                    #redirect_uri="https://ohmyroute.com/en",
                    #redirect_uri="http://localhost:8501/en",
                    redirect_uri="https://oh-my-route.streamlit.app/en",
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
                "<h1 style='text-align: center; font-size: 55px; font-weight: normal;'>Hello, welcome!</h1>",
                unsafe_allow_html=True)

            add_vertical_space(1)
            st.image('https://i.ibb.co/640DHC7/sitebanneringles.png')

            add_vertical_space(1)
            st.markdown(
                "<h1 style='text-align: center; font-size: 36px; font-weight: normal;'>Improve your business logistics <br>in 4 steps!</h1>",
                unsafe_allow_html=True)
            add_vertical_space(1)
            col16, col17, col18, col30 = st.columns(4)
            with col16:
                st.image('https://i.ibb.co/NTzTf3v/caixa-1.png', use_column_width=True)

            with col17:
                st.image('https://i.ibb.co/PmRJJ3x/caixa-2.png', use_column_width=True)

            with col18:
                st.image('https://i.ibb.co/x3Q1K43/caixa-3.png', use_column_width=True)

            with col30:
                st.image('https://i.ibb.co/jhWtVSB/caixa-4.png', use_column_width=True)

            add_vertical_space(3)
            col1, col2 = st.columns(2)
            with col1:
                video_url = "https://www.youtube.com/embed/YYWUaLNGRc4"  # Note: Use o link "embed" do YouTube
                st.video(video_url)

            with col2:
                st.markdown(
                    "<h1 style='text-align: center; font-size: 36px; font-weight: normal;'>What is Oh My Route?</h1>",
                    unsafe_allow_html=True)
                st.markdown(
                    "<h2 style='text-align: center; font-size: 27px; font-weight: normal;'><strong>Here's how it works</strong></h2>",
                    unsafe_allow_html=True)
                st.markdown(
                    "<h2 style='text-align: center; font-size: 22px; font-weight: normal;'>It is an online tool for "
                    "route optimization, especially aimed at small and medium-sized companies. <br> <br>With it, "
                    "users can enter several addresses and immediately get the most efficient routes.</h2>",
                    unsafe_allow_html=True)

            add_vertical_space(2)
            col11, col12, col13 = st.columns([1, 3, 1])
            with col12:
                st.image('https://i.ibb.co/ZT1P8Bp/iconespeqenos.png', use_column_width=True)
            col51, col52, col53 = st.columns([1, 10, 1])
            with col52:
                st.markdown(
                    "<h2 style='text-align: center; font-size: 30px; font-weight: normal;'>The <strong>Oh My Route</strong> offers the "
                    "the most comprehensive and effective route optimizer available, reducing your logistics costs!</h2>",
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
                            "<h1 style='text-align: left; font-size: 25px; font-weight: normal;line-height: 0;'><strong>Do you have any questions?</strong></h1>"
                            "<h1 style='text-align: left; font-size: 20px; font-weight: normal;line-height: 1;'>Contact us and find out more about how we can improve your logistics</h1>",
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
                            st.link_button("**Send e-mail**", f"mailto:{email_address}")


def pagina_instrucoes_de_uso():
    st.title('**Instructions for use**')

    st.header('Demo Video', divider='blue')
    # Presumindo que você tenha um vídeo para inserir, use st.video('url_do_seu_vídeo')
    #st.write('Assista ao vídeo abaixo para uma rápida demonstração de como utilizar a ferramenta:')
    st.write('Soon...')
    # Exemplo: st.video('https://www.linkdoseuvídeo.com')

    add_vertical_space(20)

    st.header('Important Info', divider='blue')
    st.write("""
    - **Address limit**: You can calculate routes for up to 100 addresses at a time.
    - **Credit Consumption**: Each route calculation consumes one credit per delivery.
    - **Initial Credits**: New users receive 30 free credits to test the tool.
    - **Add Credits**: To buy more credits, go to the "Add Credits" page.
    - **Credit Validity**: All credits purchased are valid for 90 days. Important: the validity of all your credits is reset with each new purchase, extending the period of use for a further 90 days from that date.
    - **Address Accuracy**: To ensure the best experience, please enter addresses as accurately as possible. The tool cannot be held responsible for addresses that are not found.
    """)

    st.header('How to calculate a route', divider='blue')
    st.write("""
    Follow the steps below to calculate your delivery route efficiently:

    1. **Access the Route Calculation Page**: Navigate to the page dedicated to route calculation.
    2. **Departure Address**: Enter the departure address for your deliveries.
    3. **Number of Deliverers/Trips**: Define how many deliverers are available or how many trips you want to make.
    4. **Load Limit**: Set a load limit for the vehicle, which can be in weight or volume. Always keep the same unit of measurement for consistency.
    5. **Optimization Model**: Choose between the load optimization model, which optimally distributes the load among the deliverers, and the delivery model, which divides the deliveries evenly, regardless of the load.
    6. **Address Spreadsheet**: Download the spreadsheet template provided, fill it in with the delivery addresses according to the instructions and upload it to the system.
    7. **Confirmation and Calculation**: Check the information entered and proceed with calculating the routes.
    8. **Download and Interactive Map**: After calculation, download the routes and use the interactive map to visualize the sequence of deliveries and confirm the accuracy of the addresses.

    By following these steps, you will maximize the efficiency of your deliveries and ensure the best use of your resources.
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
        "<h1 style='text-align: center; font-size: 55px; font-weight: normal;'>Your deliveries can go further</h1>",
        unsafe_allow_html=True)

    st.markdown(
        "<h1 style='text-align: center; font-size: 38px; font-weight: normal;'>Get more tickets</h1>",
        unsafe_allow_html=True)

    add_vertical_space(1)
    col1, col4, col2, col5, col3 = st.columns([20, 1, 20, 1, 20])

    with col1:
        col9, col10, col11 = st.columns([1, 10, 1])
        col10.image('https://i.ibb.co/m68k8wz/Bronzeen.png', use_column_width=True)
        with stylable_container(
                key="green_button_buy_10",
                css_styles="""
                    a[data-testid="baseLinkButton-secondary"] {
                        width: 100%;
                        background-color: #016bce;
                    }
                    """,
        ):
            st.link_button("**Buy**", "https://buy.stripe.com/7sI8xFc8U72N98Y003")

    with col2:
        col6, col7, col8 = st.columns([1, 10, 1])
        col7.image('https://i.ibb.co/DVBkn5t/prataen.png', use_column_width=True)
        with stylable_container(
                key="green_button_buy_45",
                css_styles="""
                            a[data-testid="baseLinkButton-secondary"] {
                                width: 100%;
                                background-color: #016bce;
                            }
                            """,
        ):
            st.link_button("**Buy**", "https://buy.stripe.com/dR65lt3Cofzjdpe28c")

    with col3:
        col12, col13, col14 = st.columns([1, 10, 1])
        col13.image('https://i.ibb.co/dmT4dYf/golden.png', use_column_width=True)
        with stylable_container(
                key="green_button_buy_80",
                css_styles="""
                            a[data-testid="baseLinkButton-secondary"] {
                                width: 100%;
                                background-color: #016bce;
                            }
                            """,
        ):
            st.link_button("**Buy**", "https://buy.stripe.com/aEUbJRc8U4UF1Gw005")

    st.subheader("", divider='blue')
    st.markdown("""
    **Note**: Tickets are valid for 90 days from the date of purchase. In addition, when you purchase more tickets, the validity of the tickets you already have is extended for the next 90 days as well.
    """, unsafe_allow_html=True)
    add_vertical_space(3)
    with stylable_container(
            key="green_button_",
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
                    "<h1 style='text-align: left; font-size: 25px; font-weight: normal;line-height: 0;'><strong>Do you have any questions?</strong></h1>"
                    "<h1 style='text-align: left; font-size: 20px; font-weight: normal;line-height: 1;'>Contact us and find out more about how we can improve your logistics</h1>",
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
                    st.link_button("**Send e-mail**", f"mailto:{email_address}")


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
            if st.button("Route calculation"):
                st.session_state.pagina_atual = 'pagina_principal'
            if st.button("Get tickets"):
                st.session_state.pagina_atual = 'compra_creditos'
            if st.button("Instructions for use"):
                st.session_state.pagina_atual = 'instrucoes_de_uso'
            if st.button("Logout"):
                del st.session_state["auth"]
                del st.session_state["token"]
                st.rerun()

        add_vertical_space(1)
        st.header('Tickets', divider='blue')
        add_vertical_space(1)
        creditos, validade = atualizar_creditos_usuario()
        col1, col2 = st.columns(2)
        col1.metric(label="Quantity", value=creditos)
        col2.metric(label="Valid until", value=validade)
        style_metric_cards(border_left_color='#007bff', background_color='#2B2B3B', border_color='#2B2B3B')

    if st.session_state.pagina_atual == 'pagina_principal':
        pagina_principal()
    elif st.session_state.pagina_atual == 'instrucoes_de_uso':
        pagina_instrucoes_de_uso()
    elif st.session_state.pagina_atual == 'compra_creditos':
        pagina_compra_creditos()


def app():
    st.set_page_config(layout='wide', page_title='Oh My Route', page_icon='https://i.ibb.co/pf2spMy/Layer-4a.png', initial_sidebar_state='expanded')

    controle_login()

    if "auth" in st.session_state:
        seletor_paginas()


app()
