import requests
import streamlit as st
from math import radians, cos, sin, sqrt, atan2
import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
import math
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from itertools import permutations
from ortools.constraint_solver import routing_enums_pb2, pywrapcp
from itertools import permutations
import os

API_KEY = st.secrets['API_KEY']


@st.cache_data(ttl='30d', max_entries=10000, persist=True)
def obter_coordenadas(endereco, chave_api):
    """
    Converte um endereço em coordenadas geográficas usando a Geocoding API do Google Maps.

    Parâmetros:
    endereco: O endereço que você deseja converter.
    chave_api: Sua chave de API do Google Maps.
    """

    url = "https://maps.googleapis.com/maps/api/geocode/json"

    parametros = {
        'address': endereco,
        'key': chave_api
    }

    resposta = requests.get(url, params=parametros)

    if resposta.status_code == 200:
        dados_resposta = resposta.json()

        if dados_resposta['status'] == 'OK':
            coordenadas = dados_resposta['results'][0]['geometry']['location']
            return coordenadas
        else:
            return None
    else:
        return None


@st.cache_data(ttl='30d', max_entries=10000, persist=True)
def calcular_distancia_tempo(origem, destino, chave_api):
    """
    Calcula a distância em metros e o tempo de viagem em segundos entre dois endereços
    usando a Directions API do Google Maps.

    Parâmetros:
    origem: Endereço de origem.
    destino: Endereço de destino.
    chave_api: Sua chave de API do Google Maps.
    """

    url = "https://maps.googleapis.com/maps/api/directions/json"

    parametros = {
        'origin': origem,
        'destination': destino,
        'key': chave_api
    }

    resposta = requests.get(url, params=parametros)

    if resposta.status_code == 200:
        dados_resposta = resposta.json()

        if dados_resposta['status'] == 'OK':
            rota = dados_resposta['routes'][0]['legs'][0]
            distancia_metros = rota['distance']['value']
            duracao_segundos = rota['duration']['value']
            return distancia_metros, duracao_segundos
        else:
            return "Erro: não foi possível calcular a rota.", None
    else:
        return "Erro na requisição: HTTP Status " + str(resposta.status_code), None


def calcular_distancia_haversine(coord1, coord2):
    """
    Calcula a distância entre dois pontos geográficos dados por suas coordenadas (latitude e longitude)
    usando a fórmula de Haversine.

    Parâmetros:
    coord1: Tupla contendo a latitude e longitude do primeiro ponto (lat1, lon1).
    coord2: Tupla contendo a latitude e longitude do segundo ponto (lat2, lon2).

    Retorna:
    Distância entre os dois pontos em metros.
    """

    R = 6371000

    lat1, lon1 = map(radians, coord1)
    lat2, lon2 = map(radians, coord2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distancia = R * c

    return distancia


def aplicar_obter_coordenadas(row, chave_api):
    endereco = row['Endereço']
    resultado = obter_coordenadas(endereco, chave_api)
    if isinstance(resultado, dict):
        return pd.Series([resultado.get('lat'), resultado.get('lng')])
    else:
        return pd.Series([None, None])


def clusterizar_rotas(df_enderecos, n_entregadores, carga_maxima_veiculos, nova_clusterizacao=None):
    x = df_enderecos[['Latitude', 'Longitude']].to_numpy()

    grupos_de_entrega = max(math.ceil(df_enderecos['Carga'].sum()/carga_maxima_veiculos), n_entregadores)

    if nova_clusterizacao is None:
        kmeans = KMeans(n_clusters=grupos_de_entrega, random_state=42).fit(x)
    else:
        kmeans = KMeans(n_clusters=nova_clusterizacao, random_state=42).fit(x)

    df_enderecos['Cluster'] = kmeans.labels_

    return df_enderecos


def cluster_carga_otimizada(df, limite_carga):
    df_contagem_cluster_carga = df.groupby('Cluster').agg(
        {'Carga': 'sum', 'Latitude': 'mean', 'Longitude': 'mean'}).reset_index()

    clusters_excedidos = df_contagem_cluster_carga[df_contagem_cluster_carga['Carga'] > limite_carga]

    for index, cluster in clusters_excedidos.iterrows():
        cargas_cluster = df[df['Cluster'] == cluster['Cluster']].sort_values(by='Carga')
        total_carga = cluster['Carga']

        for index_carga, carga in cargas_cluster.iterrows():
            nova_carga = total_carga - carga['Carga']

            # Se a carga removida deixa o total de carga do cluster igual ao limite, permitir a realocação
            if nova_carga >= limite_carga:
                cluster_destino = find_closest_cluster(df_contagem_cluster_carga, cluster, carga, limite_carga)

                if cluster_destino is not None:
                    df.at[index_carga, 'Cluster'] = cluster_destino['Cluster']
                    df_contagem_cluster_carga.at[cluster_destino.name, 'Carga'] += carga['Carga']
                    total_carga = nova_carga
                else:
                    break

    return df


def find_closest_cluster(df_cluster, cluster_atual, carga, limite_carga):
    df_cluster['Dist'] = np.sqrt((df_cluster['Latitude'] - cluster_atual['Latitude']) ** 2 + (
                df_cluster['Longitude'] - cluster_atual['Longitude']) ** 2)
    df_cluster_disponivel = df_cluster[(df_cluster['Carga'] + carga['Carga']) <= limite_carga]

    if len(df_cluster_disponivel) > 0:
        return df_cluster_disponivel.nsmallest(1, 'Dist').iloc[0]
    else:
        return None


def aglutinar_clusters_proximos(df, limite_carga, n_entregas):
    # Calcula novamente os centros dos clusters e suas cargas totais após qualquer otimização anterior
    df_contagem_cluster_carga = df.groupby('Cluster').agg(
        {'Carga': 'sum', 'Latitude': 'mean', 'Longitude': 'mean'}).reset_index()

    # Sinaliza se alguma aglutinação foi realizada
    mudancas = True
    while mudancas:
        mudancas = False
        for index, cluster_atual in df_contagem_cluster_carga.iterrows():
            # Verifica se a quantidade de clusters é igual ao número de entregadores
            if len(df_contagem_cluster_carga['Cluster'].unique()) <= n_entregas:
                break  # Encerra o loop se a quantidade mínima de clusters for atingida

            # Ignora a carga do cluster atual para a busca, já que queremos encontrar um destino possível para o cluster
            cluster_destino = find_closest_cluster(df_contagem_cluster_carga.drop(index), cluster_atual, {'Carga': 0},
                                                   limite_carga)

            if cluster_destino is not None and (cluster_atual['Carga'] + cluster_destino['Carga']) <= limite_carga:
                # Atualiza os registros no df original para refletir a nova atribuição de cluster
                df.loc[df['Cluster'] == cluster_atual['Cluster'], 'Cluster'] = cluster_destino['Cluster']

                # Atualiza o estado para refletir a mudança e permitir outra iteração se necessário
                mudancas = True

                # Atualiza a carga total no DataFrame auxiliar para refletir a aglutinação
                df_contagem_cluster_carga.at[
                    df_contagem_cluster_carga[df_contagem_cluster_carga['Cluster'] == cluster_destino['Cluster']].index[
                        0], 'Carga'] += cluster_atual['Carga']
                df_contagem_cluster_carga = df_contagem_cluster_carga.drop(index)
                df_contagem_cluster_carga.reset_index(drop=True, inplace=True)
                break

    # Após a conclusão das aglutinações, renumera os clusters
    clusters_unicos = df['Cluster'].unique()
    clusters_unicos.sort()  # Garante que a ordem seja mantida
    mapeamento_clusters = {cluster_antigo: novo_cluster for novo_cluster, cluster_antigo in
                           enumerate(clusters_unicos)}

    # Atualiza os clusters no DataFrame com os novos identificadores
    df['Cluster'] = df['Cluster'].map(mapeamento_clusters)
    return df


def otimizar_entregas(df, n_entregas, limite_carga, tipo):
    if tipo == 'carga':
        df = clusterizar_rotas(df, n_entregas, limite_carga)

        grupos_de_entrega = max(math.ceil(df['Carga'].sum() / limite_carga), n_entregas)

        cargas_cluster = df.groupby('Cluster').agg({'Carga': 'sum'}).reset_index()
        cluesters_acima = cargas_cluster[cargas_cluster['Carga'] > limite_carga]

        while not cluesters_acima.empty:
            df = cluster_carga_otimizada(df, limite_carga)

            cargas_cluster = df.groupby('Cluster').agg({'Carga': 'sum'}).reset_index()
            cluesters_acima = cargas_cluster[cargas_cluster['Carga'] > limite_carga]

            if not cluesters_acima.empty:
                grupos_de_entrega += 1
                df = clusterizar_rotas(df, n_entregas, limite_carga, grupos_de_entrega)

        df = aglutinar_clusters_proximos(df, limite_carga, n_entregas)

    else:
        df['Carga'] = 1
        df = clusterizar_rotas(df, n_entregas, 1000000)

        grupos_de_entrega = max(math.ceil(df['Carga'].sum() / 1000000), n_entregas)

        limite_carga = math.ceil(df['Carga'].sum() * 1.1 / n_entregas)
        cargas_cluster = df.groupby('Cluster').agg({'Carga': 'sum'}).reset_index()
        cluesters_acima = cargas_cluster[cargas_cluster['Carga'] > limite_carga]

        while not cluesters_acima.empty:
            df = cluster_carga_otimizada(df, limite_carga)

            cargas_cluster = df.groupby('Cluster').agg({'Carga': 'sum'}).reset_index()
            cluesters_acima = cargas_cluster[cargas_cluster['Carga'] > limite_carga]

            if not cluesters_acima.empty:
                grupos_de_entrega += 1
                df = clusterizar_rotas(df, n_entregas, limite_carga, grupos_de_entrega)

    return df


def criar_matriz_distancia(pontos):
    """Cria uma matriz de distância entre pontos usando a distância Haversine."""

    n = len(pontos)
    matriz_distancia = {}
    for i in range(n):
        for j in range(n):
            if i == j:
                matriz_distancia[i, j] = 0
            else:
                matriz_distancia[i, j] = calcular_distancia_haversine(pontos[i], pontos[j])
    return matriz_distancia


def calcular_distancia_total(permutacao, matriz_distancia):
    distancia_total = 0
    for i in range(len(permutacao) - 1):
        distancia_total += matriz_distancia[permutacao[i], permutacao[i + 1]]
    # Adiciona a distância de retorno ao ponto inicial
    distancia_total += matriz_distancia[permutacao[-1], permutacao[0]]
    return distancia_total


def resolver_tsp_forca_bruta(pontos, matriz_distancia):
    todas_permutacoes = permutations(range(1, len(pontos)))  # Ignora o ponto de partida para permutações
    melhor_distancia = float('inf')
    melhor_rota = None
    for permutacao in todas_permutacoes:
        # Adiciona o ponto de partida ao início e ao fim da permutação
        rota_atual = (0,) + permutacao + (0,)
        distancia_atual = calcular_distancia_total(rota_atual, matriz_distancia)
        if distancia_atual < melhor_distancia:
            melhor_distancia = distancia_atual
            melhor_rota = rota_atual
    return [melhor_rota, melhor_distancia]


@st.cache_data(ttl='1d')
def resolver_tsp_por_cluster(df, ponto_partida):
    rotas_por_cluster = []

    for cluster in sorted(df['Cluster'].unique()):
        df_cluster = df[df['Cluster'] == cluster]
        pontos = [ponto_partida] + df_cluster[['Latitude', 'Longitude']].values.tolist()

        if len(pontos) <= 11:
            # Resolve TSP por força bruta
            matriz_distancia = criar_matriz_distancia(pontos)
            melhor_rota, melhor_distancia = resolver_tsp_forca_bruta(pontos, matriz_distancia)
            # Converte índices de melhor_rota para códigos do df_cluster
            rota_codigos = ['Partida'] + [df_cluster.iloc[i - 1]['Código'] for i in melhor_rota[1:-1]] + ['Retorno']
            rotas_por_cluster.append(rota_codigos)
        else:
            manager = pywrapcp.RoutingIndexManager(len(pontos), 1, 0)
            routing = pywrapcp.RoutingModel(manager)

            matriz_distancia = criar_matriz_distancia(pontos)
            distancia_callback_index = routing.RegisterTransitCallback(lambda i, j: matriz_distancia[i, j])
            routing.SetArcCostEvaluatorOfAllVehicles(distancia_callback_index)

            search_parameters = pywrapcp.DefaultRoutingSearchParameters()
            search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC)
            search_parameters.local_search_metaheuristic = (routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)

            search_parameters.time_limit.FromSeconds(len(pontos)*5)

            solucao = routing.SolveWithParameters(search_parameters)
            rota_cluster = []

            if solucao:
                index = routing.Start(0)
                while not routing.IsEnd(index):
                    node_index = manager.IndexToNode(index)
                    if node_index == 0:
                        rota_cluster.append('Partida')
                    else:
                        rota_cluster.append(df_cluster.iloc[node_index - 1]['Código'])
                    index = solucao.Value(routing.NextVar(index))
                rota_cluster.append('Retorno')
            rotas_por_cluster.append(rota_cluster)

    return rotas_por_cluster


def calcular_tempo_distancia_por_rota(matriz_entregas, endereco_origem, df_entregas_otimizadas):
    rotas = []
    for rota in range(len(matriz_entregas)):
        distancia = 0
        tempo = 0
        distancia_tempo = {}
        for n, codigo in enumerate(matriz_entregas[rota][:-1]):
            if n == 0:
                origem = endereco_origem
            else:
                origem = df_entregas_otimizadas[df_entregas_otimizadas['Código'] == codigo]['Endereço'].values[0]

            if n == len(matriz_entregas[rota][:-1]) - 1:
                destino = endereco_origem
            else:
                destino = df_entregas_otimizadas[df_entregas_otimizadas['Código'] == matriz_entregas[rota][n + 1]][
                    'Endereço'].values[0]

            dist, temp = calcular_distancia_tempo(origem, destino, API_KEY)
            distancia += dist
            tempo += temp
        distancia_tempo['tempo'] = tempo + 600 * n
        distancia_tempo['distancia'] = distancia
        rotas.append(distancia_tempo)
    return rotas



def construir_df_final(rotas_por_cluster, df_entregas_otimizadas, temp_dist, ponto_partida):
    for n in range(len(rotas_por_cluster)):
        rotas_por_cluster[n] = rotas_por_cluster[n][1:-1]

    df_informacoes_compiladas = df_entregas_otimizadas.groupby('Cluster').first().reset_index()[['Cluster']]
    df_informacoes_compiladas['Rota por codigo'] = rotas_por_cluster
    df_informacoes_compiladas['Distancia tempo'] = temp_dist
    lista_enderecos = []
    lista_coordenadas = []

    for cluster in df_informacoes_compiladas['Cluster'].unique():
        sequencia_enderecos = []
        sequencia_coordenadas = [ponto_partida]

        for codigo in \
        df_informacoes_compiladas[df_informacoes_compiladas['Cluster'] == cluster]['Rota por codigo'].values[0]:
            sequencia_enderecos.append(
                df_entregas_otimizadas[df_entregas_otimizadas['Código'] == codigo]['Endereço'].values[0])
            coordenadas_endereco = [
                df_entregas_otimizadas[df_entregas_otimizadas['Código'] == codigo]['Latitude'].values[0],
                df_entregas_otimizadas[df_entregas_otimizadas['Código'] == codigo]['Longitude'].values[0]]
            sequencia_coordenadas.append(coordenadas_endereco)

        lista_coordenadas.append(sequencia_coordenadas)
        lista_enderecos.append(sequencia_enderecos)

    df_informacoes_compiladas['enderecos'] = lista_enderecos
    df_informacoes_compiladas['coordenadas'] = lista_coordenadas

    return df_informacoes_compiladas


def formatar_tempo(tempo_segundos):
    # Converte tempo de segundos para horas e minutos
    horas = tempo_segundos // 3600
    minutos = (tempo_segundos % 3600) // 60

    if horas == 0:
        return f"{minutos} min"
    else:
        return f"{horas} h e {minutos} min"


def gerar_pdf_para_cluster(df, directory, languege):
    styles = getSampleStyleSheet()

    if not os.path.exists(directory):
        os.makedirs(directory)

    for i, row in df.iterrows():
        nome_entrega = {'en': 'Delivery', 'br': 'Entrega'}
        doc = SimpleDocTemplate(f"{directory}/{nome_entrega[languege]}_{i}.pdf", pagesize=letter)
        elements = []

        # Título
        title = Paragraph(nome_entrega[languege], styles['Title'])
        elements.append(title)

        # Subtítulo - Tempo estimado e Distância
        tempo_horas = formatar_tempo(row['Distancia tempo']['tempo'])
        distancia_km = row['Distancia tempo']['distancia'] / 1000
        distancia_mi = row['Distancia tempo']['distancia'] / 1609
        tempo_nome = {'br': 'Tempo estimado', 'en': 'Estimated time'}
        subtitle_tempo = Paragraph(f"<b>{tempo_nome[languege]}:</b> {tempo_horas}",
                                   ParagraphStyle('tempoPercursoStyle', parent=styles['Normal'], fontSize=12,
                                                  leading=14))
        percurso_estimado_nome = {'br': 'Percurso estimado', 'en': 'Estimated route'}
        distancia = {'en': distancia_mi, 'br': distancia_km}
        kmmi = {'en': 'mi', 'br': 'km'}
        subtitle_distancia = Paragraph(f"<b>{percurso_estimado_nome[languege]}:</b> {distancia[languege]:.2f} {kmmi[languege]}",
                                       ParagraphStyle('tempoPercursoStyle', parent=styles['Normal'], fontSize=12,
                                                      leading=14))
        elements.append(subtitle_tempo)
        elements.append(subtitle_distancia)

        # Adiciona um espaço antes da tabela
        elements.append(Spacer(1, 12))

        # Tabela
        colunas_nomes_codigo = {'br': 'Código', 'en': 'Code'}
        colunas_nomes_endereco = {'br': 'Endereço', 'en': 'Address'}
        data = [[colunas_nomes_codigo[languege], colunas_nomes_endereco[languege]]] + list(zip(row['Rota por codigo'], row['enderecos']))
        table = Table(data, colWidths=[100, 350], repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        elements.append(table)

        # Constrói o PDF
        doc.build(elements)
