from collections import defaultdict
from typing import List

from sidermit.optimization.preoptimization import ExtendedEdge, ExtendedNode
from sidermit.optimization.preoptimization import StopNode, RouteNode
from sidermit.publictransportsystem import RouteType, Route

defaultdict2_float = defaultdict(lambda: defaultdict(float))
list_suc = defaultdict(List[ExtendedEdge])
list_lab = defaultdict(float)
list_f = defaultdict(float)
list_elemental_path = List[ExtendedNode]
defaultdict_elemental_path = defaultdict(List[list_elemental_path])

dic_hyperpaths = defaultdict(lambda: defaultdict(lambda: defaultdict(List[list_elemental_path])))
dic_labels = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
dic_successors = defaultdict(lambda: defaultdict(lambda: defaultdict(List[ExtendedEdge])))
dic_frequency = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
dic_Vij = defaultdict(lambda: defaultdict(float))
dic_assigment = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
dic_f = defaultdict(float)

dic_boarding = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
dic_alighting = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

dic_loaded_section = defaultdict(float)


class Assignment:

    def __init__(self):
        pass

    @staticmethod
    def get_assignment(hyperpaths: dic_hyperpaths, labels: dic_labels, p: float, vp: float, spa: float,
                       spv: float) -> dic_assigment:
        """
        to distribute trips of all OD pair in each StopNode of the Origin
        :param vp: Walking speed [km/h]
        :param spv: Subjetive value of in-vehicle time savings [US$/h]
        :param spa: Subjetive value of access time savings [US$/h]
        :param hyperpaths: Dic[origin: CityNode][destination: CityNode][StopNode] = List[List[ExtendedNodes]].
        Each List[ExtendedNodes] represent a elemental path.
        :param labels: dic[origin: CityNode][destination: CityNode][ExtendedNode] = Label [
        :param p: width [m] of all CityNode
        :return: dic[origin: CityNode][destination: CityNode][Stop: StopNode] = %V_OD
        """

        assignment = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

        for origin in hyperpaths:
            for destination in hyperpaths[origin]:

                # paradero de d = 1
                stop1 = None
                # otro paradero ( su d puede ser o no 1)
                stop2 = None

                # encontramos paradero de d = 1
                for stop in hyperpaths[origin][destination]:
                    if stop.mode.d == 1:
                        if stop1 is None:
                            stop1 = stop
                        else:
                            stop2 = stop
                    else:
                        stop2 = stop

                # solo tiene una parada
                if stop1 is None or stop2 is None:
                    if stop1 is not None:
                        assignment[origin][destination][stop1] = 100
                    if stop2 is not None:
                        assignment[origin][destination][stop2] = 100
                # existen ambas paradas
                else:
                    # paradero con d = 1 es de etiqueta minima
                    if labels[origin][destination][stop1] <= labels[origin][destination][stop2]:
                        # calculamos caminata de indiferencia
                        d = vp * (labels[origin][destination][stop2] - labels[origin][destination][stop1]) / (spa / spv)

                        # caminata de indiferencia es mayor a la zona de influencia de stop1
                        if d >= p / 2:
                            assignment[origin][destination][stop1] = 100

                        # caminata de indiferencia es menor a la zona de influencia de stop1
                        else:

                            # zona de influencia de stop_2
                            zona_stop_2 = p / stop2.mode.d

                            # encontraremos linea de stop 2
                            position = 0
                            # reconoceremos posición de todos los paraderos ubicado a la derecha de stop1
                            for i in range(int(stop2.mode.d / 2)):
                                if i == 0:
                                    position = zona_stop_2 / 2
                                else:
                                    position = position + zona_stop_2
                                # encontramos un paradero de stop2 que esta ubicado mas lejos que la distancia de
                                # indiferencia
                                if position > d:
                                    assignment[origin][destination][stop1] = (2 * d + (position - d)) / p * 100
                                    assignment[origin][destination][stop2] = 100 - assignment[origin][destination][
                                        stop1]
                                    break
                            # si no se encontro paradero mas lejos a la distancia de indiferencia asignar to do a stop1
                            if position < d:
                                assignment[origin][destination][stop1] = 100
                    else:
                        # si parametro d de stop2 es impar
                        if stop2.mode.d % 2 == 1:
                            assignment[origin][destination][stop2] = 100
                        else:
                            # calculamos caminata de indiferencia
                            d = vp * (labels[origin][destination][stop1] - labels[origin][destination][stop2]) / (
                                    spa / spv)

                            # necesitamos posicion del primer paradero stop2 a la derecha del centro
                            position = (p / stop2.mode.d) * 0.5

                            if d >= position:
                                assignment[origin][destination][stop2] = 100
                            else:
                                assignment[origin][destination][stop1] = (position - d) / p * 100
                                assignment[origin][destination][stop2] = 100 - assignment[origin][destination][
                                    stop1]
        return assignment

    @staticmethod
    def get_alighting_and_boarding(Vij: dic_Vij, hyperpaths: dic_hyperpaths, successors: dic_successors,
                                   assignment: dic_assigment, f: dic_f) -> (dic_boarding, dic_alighting):
        """
        to get two matrix (z and v) with alighting and boarding for vehicle in each stop of all routes
         :param successors: dic[origin: CityNode][destination: CityNode] [ExtendedNode] = List[ExtendedEdge],
        List[ExtendedEdge] represent all successors edge for each ExtendedNode in a OD pair.
        :param Vij: dic[origin: CityNode][destination: CityNode] = vij [pax/hr]
        :param hyperpaths: Dic[origin: CityNode][destination: CityNode][StopNode] = List[List[ExtendedNodes]].
        Each List[ExtendedNodes] represent a elemental path to connect a origin and destination
        :param assignment: dic[origin: CityNode][destination: CityNode][Stop: StopNode] =%V_OD
        :param f: dic[route_id] = frequency [veh/hr]
        :return: dic[route_id][direction][stop: StopNode] = pax [pax/veh],
         dic[route_id][direction][stop: StopNode] = pax [pax/veh]
        """

        z = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
        v = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

        for origin in hyperpaths:
            for destination in hyperpaths[origin]:
                # viajes del par OD
                vod = Vij[origin][destination]
                for stop in hyperpaths[origin][destination]:
                    # viajes de todas las rutas elementales que salen de esta parada
                    vod_s = vod * assignment[origin][destination][stop] / 100

                    if vod_s == 0:
                        continue

                    paths = []

                    for suc in successors[origin][destination][stop]:
                        nodej = suc.nodej
                        paths.append((stop, nodej, vod_s))

                    while len(paths) != 0:
                        nodei, nodej, pax = paths.pop(0)

                        dis_pax = pax

                        if isinstance(nodei, StopNode):
                            # reportar subidas
                            if isinstance(nodej, RouteNode):

                                f_acum = 0

                                for suc in successors[origin][destination][nodei]:
                                    f_acum += f[suc.nodej.route.id]

                                dis_pax = pax * (f[nodej.route.id] / f_acum)

                                z[nodej.route.id][nodej.direction][nodei] += dis_pax

                        if isinstance(nodei, RouteNode):
                            # reportar bajadas
                            if isinstance(nodej, StopNode):
                                v[nodei.route.id][nodei.direction][nodej] += dis_pax

                        # agregar nuevos elementos a paths, salvo que hayan llegado a destino
                        if isinstance(nodej, StopNode) and nodej.city_node == destination:
                            continue

                        else:
                            for suc in successors[origin][destination][nodej]:
                                paths.append((nodej, suc.nodej, dis_pax))

        for route_id in z:
            for direction in z[route_id]:
                for stop_node in z[route_id][direction]:
                    if f[route_id] == 0:
                        continue
                    else:
                        z[route_id][direction][stop_node] = z[route_id][direction][stop_node] / (
                            f[route_id])
        for route_id in v:
            for direction in v[route_id]:
                for stop_node in v[route_id][direction]:
                    if f[route_id] == 0:
                        continue
                    else:
                        v[route_id][direction][stop_node] = v[route_id][direction][stop_node] / (
                            f[route_id])

        return z, v

    @staticmethod
    def str_boarding_alighting(z: dic_boarding, v: dic_alighting) -> str:
        """
        to print boarding and alighting
        :param z: boarding, dic[route_id][direction][stop: StopNode] = pax [pax/veh]
        :param v: alighting, dic[route_id][direction][stop: StopNode] = pax [pax/veh]
        :return:
        """
        line = "\nBoarding and Alighting information:"
        for route_id in z:
            line += "\nNew route: {}".format(route_id)
            line += "\n\tBoarding:"
            for direction in z[route_id]:
                line += "\n\t\tDirection: {}".format(direction)
                for stop_node in z[route_id][direction]:
                    line += "\n\t\t\tStop {}-{}: {:.2f}[pax/veh]".format(stop_node.mode.name,
                                                                         stop_node.city_node.graph_node.name,
                                                                         z[route_id][direction][stop_node])
            line += "\n\tAlighting:"
            for direction in v[route_id]:
                line += "\n\t\tDirection: {}".format(direction)
                for stop_node in v[route_id][direction]:
                    line += "\n\t\t\tStop {}-{}: {:.2f}[pax/veh]".format(stop_node.mode.name,
                                                                         stop_node.city_node.graph_node.name,
                                                                         v[route_id][direction][stop_node])
        return line

    @staticmethod
    def most_loaded_section(routes: List[Route], z: dic_boarding, v: dic_alighting,
                            f: list_f) -> dic_loaded_section:
        """
        to get  most loaded section for each routes
        :param f: dic[route_id] = frequency [veh/hr]
        :param routes: List[Route]
        :param z: boarding, dic[route_id][direction][stop: StopNode] = pax [pax/veh]
        :param v: alighting, dic[route_id][direction][stop: StopNode] = pax [pax/veh]
        :return: dic[route_id] = pax [pax/veh]
        """

        most_loaded_section = defaultdict(float)

        for route in routes:

            route_id = route.id
            node_sequence_i = route.nodes_sequence_i
            node_sequence_r = route.nodes_sequence_r

            # caso circular
            if route._type == RouteType.CIRCULAR:

                # circular con sentido de ida
                if len(node_sequence_i) > 0:
                    node_sequence = node_sequence_i
                    direction = "I"
                # circular con sentido de vuelta
                else:
                    node_sequence = node_sequence_r
                    direction = "R"

                qi = [0]
                for i in node_sequence:
                    zi = 0
                    vi = 0
                    for stop_node in z[route_id][direction]:
                        if str(stop_node.city_node.graph_node.id) == str(i):
                            zi = z[route_id][direction][stop_node]
                            break
                    for stop_node in v[route_id][direction]:
                        if str(stop_node.city_node.graph_node.id) == str(i):
                            vi = v[route_id][direction][stop_node]
                            break
                    new_qi = qi[len(qi) - 1] + zi * f[route_id] - vi * f[route_id]
                    qi.append(new_qi)
                q = min(qi)
                ki_max = 0
                for i in range(len(qi)):
                    if i == 0:
                        continue
                    ki = (qi[i] - q) / f[route_id]
                    if ki > ki_max:
                        ki_max = ki
                most_loaded_section[route_id] = ki_max

            # caso no circular
            else:

                max_loaded_section = 0
                prev_loaded = 0

                for i in node_sequence_i:
                    zi = 0
                    vi = 0

                    for stop_node in z[route_id]["I"]:
                        if str(stop_node.city_node.graph_node.id) == str(i):
                            zi = z[route_id]["I"][stop_node]
                            break
                    for stop_node in v[route_id]["I"]:
                        if str(stop_node.city_node.graph_node.id) == str(i):
                            vi = v[route_id]["I"][stop_node]
                            break

                    prev_loaded += zi - vi

                    if prev_loaded > max_loaded_section:
                        max_loaded_section = prev_loaded

                prev_loaded = 0

                for i in node_sequence_r:

                    zi = 0
                    vi = 0

                    for stop_node in z[route_id]["R"]:
                        if str(stop_node.city_node.graph_node.id) == str(i):
                            zi = z[route_id]["R"][stop_node]
                            break
                    for stop_node in v[route_id]["R"]:
                        if str(stop_node.city_node.graph_node.id) == str(i):
                            vi = v[route_id]["R"][stop_node]
                            break

                    prev_loaded += zi - vi

                    if prev_loaded > max_loaded_section:
                        max_loaded_section = prev_loaded

                most_loaded_section[route_id] = max_loaded_section

        return most_loaded_section
