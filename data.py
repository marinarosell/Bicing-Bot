import networkx as nx
import pandas as pd
from pandas import DataFrame
from haversine import haversine
from geopy.geocoders import Nominatim
from staticmap import StaticMap, CircleMarker, Line


url_info = 'https://api.bsmsa.eu/ext/api/bsm/gbfs/v2/en/station_information'
url_status = 'https://api.bsmsa.eu/ext/api/bsm/gbfs/v2/en/station_status'
bicing = DataFrame.from_records(pd.read_json(url_info)['data']['stations'],
                                index='station_id')
bikes = DataFrame.from_records(pd.read_json(url_status)['data']['stations'],
                               index='station_id')


# classe Node: cada node del Graf és una estació i en ell guardem les
# coordenades de latitud i longitud corresponents
class Node:
    def __init__(self, lat, lon, id):
        self.lat = lat
        self.lon = lon
        self.id = id


# Retorna True si existeix un graf amb la clau de l'usuari en el diccionari i
# False, altrament
def existent(user_data):
    if 'G' in user_data:
        return True
    else:
        return False


# retorna la distància entre dues estacions (o nodes)
def distancia(node, aux):
    coor_1 = (node.lat, node.lon)
    coor_2 = (aux.lat, aux.lon)
    return haversine(coor_1, coor_2)


# Crea un graf amb totes les estacions de bicing i les arestes entre les que
# tenen distancia menor o igual a la donada. Per defecte, distancia = 1000
def create_graph(user_data, dist_=['1000']):
    dist = int(dist_[0])
    dist += dist * 0.005  # Epsilon per solucionar errors de truncament
    user_data['G'] = nx.Graph()

    for st in bicing.itertuples():  # Crea nodes i els afegeix al graf
        index = st.Index
        node = Node(st.lat, st.lon, index)
        user_data['G'].add_node(node)

    if dist != 0:
        # Crea una matriu-graella al mapa amb caselles de mida
        # distancia*distancia.
        # Busca les coordenades mínimes i màximes per fer la matriu
        alt_max = bicing['lon'].max()
        alt_min = bicing['lon'].min()
        amp_max = bicing['lat'].max()
        amp_min = bicing['lat'].min()

        # 111319m = 1 grau lat/lon
        altura = (alt_max - alt_min) * 111319 / dist
        altura = int(altura)

        amplada = (amp_max - amp_min) * 111319 / dist
        amplada = int(amplada)

        matriu = []
        for i in range(altura+1):  # numero de files
            matriu.append([])
            for j in range(amplada+1):  # numero de columnes
                matriu[i].append([])

        # Troba les arestes i afegeix els nodes a les caselles de la matriu
        for node in user_data['G']:
            fila = (node.lon - alt_min) * 111319 / dist
            fila = int(fila)
            columna = (node.lat - amp_min) * 111319 / dist
            columna = int(columna)
            # Comprova els nodes que hi ha a les 9 caselles del voltant
            for i in range(-1, 2):
                if fila == 0 and i == -1:  # Per no sortir de la matriu
                    i += 1
                if fila == altura and i == 1:
                    break
                for j in range(-1, 2):
                    if columna == 0 and j == -1:
                        j += 1
                    if columna == amplada and j == 1:
                        break
                    for vertex in matriu[fila+i][columna+j]:
                        distancia_ = distancia(node, vertex) * 1000
                        w = distancia_ / 10  # velocitat en bici: 10km/h
                        if distancia_ <= dist:
                            user_data['G'].add_edge(node, vertex, weight=w)
            matriu[fila][columna].append(node)

    return


# retorna el nombre de nodes de G
def number_nodes(user_data):
    return user_data['G'].number_of_nodes()


# retorna el nombre d'arestes de G
def number_arestes(user_data):
    return user_data['G'].number_of_edges()


# retorna el nombre de components connexos
def number_components(user_data):
    return len(list(nx.connected_components(user_data['G'])))


# Afegeix una estació al mapa
def print_marker(map, lon, lat, color, size):
    marker = CircleMarker((lon, lat), color, size)
    map.add_marker(marker)
    return map


# Afegeix una aresta al mapa
def print_line(map, lon1, lat1, lon2, lat2, color, size):
    coordinates = [[lon1, lat1], [lon2, lat2]]
    line = Line(coordinates, color, size)
    map.add_line(line)
    return map


# Crea una imatge png d'un mapa de Barcelona amb les estacions de bicing
# (nodes de G) i les arestes de G
def create_plotgraph(user_data):
    map = StaticMap(900, 900)
    G = user_data['G']
    for node in G.node:
        map = print_marker(map, node.lon, node.lat, 'black', 8)
        map = print_marker(map, node.lon, node.lat, 'red', 4)

    for edge in G.edges:
        coor_1 = edge[0]
        coor_2 = edge[1]
        map = print_line(map, coor_1.lon, coor_1.lat, coor_2.lon, coor_2.lat,
                         'red', 2)

    image = map.render()
    name = str(user_data['user']) + '_mapa.png'
    image.save(name)
    return


# Crea una imatge png d'un mapa de Barcelona amb la ruta més curta de
# l'origen al destí introduits
def create_image(route, user_data):
    map = StaticMap(900, 900)
    n = len(route)

    map = print_marker(map, route[0].lon, route[0].lat, 'black', 12)
    map = print_marker(map, route[0].lon, route[0].lat, 'white', 8)
    map = print_marker(map, route[1].lon, route[1].lat, 'black', 8)
    map = print_marker(map, route[1].lon, route[1].lat, 'red', 4)
    map = print_line(map, route[0].lon, route[0].lat, route[1].lon,
                     route[1].lat, 'blue', 2)

    for i in range(2, n-1):
        map = print_marker(map, route[i].lon, route[i].lat, 'black', 8)
        map = print_marker(map, route[i].lon, route[i].lat, 'red', 4)
        map = print_line(map, route[i-1].lon, route[i-1].lat, route[i].lon,
                         route[i].lat, 'red', 2)

    map = print_marker(map, route[n-1].lon, route[n-1].lat, 'black', 12)
    map = print_marker(map, route[n-1].lon, route[n-1].lat, 'white', 8)
    map = print_line(map, route[n-2].lon, route[n-2].lat, route[n-1].lon,
                     route[n-1].lat, 'blue', 2)

    image = map.render()
    name = str(user_data['user']) + '_ruta.png'
    image.save(name)
    return


# Retorna latitud i longitud de les dues direccions, origen i destí
def adreces(adresses):
    try:
        geolocator = Nominatim(user_agent="bicing_bot")
        adress1, adress2 = adresses.split(',')
        location1 = geolocator.geocode(adress1 + ', Barcelona')
        location2 = geolocator.geocode(adress2 + ', Barcelona')
        return (location1.latitude, location1.longitude), \
            (location2.latitude, location2.longitude)
    except:
        return None  # si no troba alguna de les adreces, retorna None


# Afegeix els nodes origen i destí al graf, amb les seves respectives arestes
def add_new_nodes(user_data, origen, desti):
    user_data['G'].add_node(origen)
    user_data['G'].add_node(desti)
    distancia_ = distancia(origen, desti) * 1000
    # Afegim la aresta de origen a final amb temps de 4km/h
    user_data['G'].add_edge(origen, desti, weight=distancia_ / 4)
    # Afegim les arestes d'origen i destí a la resta de nodes amb temps = 4km/h
    for node in user_data['G'].node:
        if node != origen and node != desti:
            distancia_1 = distancia(origen, node) * 1000
            distancia_2 = distancia(desti, node) * 1000
            user_data['G'].add_edge(origen, node, weight=distancia_1 / 4)
            user_data['G'].add_edge(desti, node, weight=distancia_2 / 4)
    return


# Esborra els nodes origen i destí del graf, amb les seves respectives arestes
def remove(user_data, origen, desti):
    user_data['G'].remove_node(origen)
    user_data['G'].remove_node(desti)
    return


# Retorna el camí més ràpid d'un origen a un destí passant per les arestes de G
def create_route(args, user_data):
    adresses = args[0]
    for i in range(1, len(args)):
        adresses = adresses + str(" ") + str(args[i])
    coords = adreces(adresses)
    if coords is None:
        return False   # escriure un missatge que l'adreça no s'ha trobat
    else:
        coord_origen, coord_desti = coords
        origen = Node(coord_origen[0], coord_origen[1], 0)
        desti = Node(coord_desti[0], coord_desti[1], 0)
        add_new_nodes(user_data, origen, desti)
        route = nx.dijkstra_path(user_data['G'], origen, desti)
        create_image(route, user_data)

        remove(user_data, origen, desti)
        return True


def distribution(args, user_data):
    requiredBikes = int(args[0])
    requiredDocks = int(args[1])

    Flow = nx.DiGraph()
    Flow.add_node('TOP')
    demand = 0

    for st in bikes.itertuples():
        index = str(st.Index)
        if st.Index not in bicing.index:
            continue
        s_idx, g_idx, t_idx = 's' + index, 'g' + index, 't' + index
        Flow.add_node(g_idx)
        Flow.add_node(s_idx)
        Flow.add_node(t_idx)

        b, d = st.num_bikes_available, st.num_docks_available
        req_bikes = max(0, requiredBikes - b)
        req_docks = max(0, requiredDocks - d)
        if req_bikes > 0:
            demand += req_bikes
            Flow.nodes[t_idx]['demand'] = req_bikes
        elif req_docks > 0:
            demand -= req_docks
            Flow.nodes[s_idx]['demand'] = - req_docks

        pos_donacio = max(0, b - requiredBikes)
        pos_recepcio = max(0, d - requiredDocks)

        Flow.add_edge('TOP', s_idx)
        Flow.add_edge(t_idx, 'TOP')
        Flow.add_edge(s_idx, g_idx, capacity=pos_donacio)
        Flow.add_edge(g_idx, t_idx, capacity=pos_recepcio)

    Flow.nodes['TOP']['demand'] = - demand
    for edge in user_data['G'].edges:
        index_origen = 'g' + str(edge[0].id)
        index_desti = 'g' + str(edge[1].id)
        # ho passem primer a km i després a metres
        weight = int(user_data['G'].edges[edge]['weight']*10)
        Flow.add_edge(index_origen, index_desti, weight=weight)
        Flow.add_edge(index_desti, index_origen, weight=weight)

    user_data['Flow'] = Flow
    try:
        error = False
        flowCost, flowDict = nx.network_simplex(Flow)
    except nx.NetworkXUnfeasible:
        error = True
        return None, False

    except:
        error = True
        return None, True
    if not error:
        # return flowCost, flowDict

        # llista amb els dos nodes per on passa el màxim flux, i el màxim flux
        # flowMax[0] = estació d'origen
        # flowMax[1] = estació final
        # flowMax[2] = nombre de bicis que es transfereixen
        # flowMax[3] = cost de moure les bici
        flowMax = [0, 0, 0, 0]
        for source in flowDict:
            if source[0] != 'g':
                continue
            index_source = int(source[1:])
            for desti, bicis in flowDict[source].items():
                if desti[0] == 'g' and bicis > 0:
                    index_desti = int(desti[1:])
                    cost = Flow.edges[source, desti]['weight']
                    if cost > flowMax[3]:
                        flowMax[0] = index_source
                        flowMax[1] = index_desti
                        flowMax[2] = bicis
                        flowMax[3] = cost

        return flowCost, flowMax
