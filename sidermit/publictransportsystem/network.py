from collections import defaultdict
from enum import Enum

import networkx as nx
import pandas as pd
from matplotlib import pyplot as plt

from sidermit.city import graph
from sidermit.publictransportsystem import TransportMode
from sidermit.exceptions import *


class RouteType(Enum):
    CUSTOM = 1
    PREDEFINED = 2


class Route:

    def __init__(self, route_id, mode_obj, nodes_sequence_i, nodes_sequence_r, stops_sequence_i,
                 stops_sequence_r, _type=RouteType.CUSTOM):
        self.id = None
        self.mode = None
        self.nodes_sequence_i = None
        self.nodes_sequence_r = None
        self.stops_sequence_i = None
        self.stops_sequence_r = None
        self._type = _type

        if route_id is None:
            raise RouteIdIsNotValidException("route_id is not valid. Try to give a value for route_id")

        # special case for circular routes
        if _type == RouteType.PREDEFINED:
            self.id = route_id
            self.mode = mode_obj
            self.nodes_sequence_i = self.sequences_to_list(nodes_sequence_i)
            self.nodes_sequence_r = self.sequences_to_list(nodes_sequence_r)
            self.stops_sequence_i = self.sequences_to_list(stops_sequence_i)
            self.stops_sequence_r = self.sequences_to_list(stops_sequence_r)

        else:
            # to valid parameters
            if self.parameters_validator(mode_obj,
                                         nodes_sequence_i, nodes_sequence_r,
                                         stops_sequence_i, stops_sequence_r):
                self.id = route_id
                self.mode = mode_obj
                self.nodes_sequence_i = self.sequences_to_list(nodes_sequence_i)
                self.nodes_sequence_r = self.sequences_to_list(nodes_sequence_r)
                self.stops_sequence_i = self.sequences_to_list(stops_sequence_i)
                self.stops_sequence_r = self.sequences_to_list(stops_sequence_r)

    def parameters_validator(self, mode_obj, nodes_sequence_i, nodes_sequence_r,
                             stops_sequence_i, stops_sequence_r):
        """
        to check all parameters
        :param mode_obj:
        :param nodes_sequence_i:
        :param nodes_sequence_r:
        :param stops_sequence_i:
        :param stops_sequence_r:
        :return:
        """
        if not isinstance(mode_obj, TransportMode):
            raise ModeIsNotValidException("mode obj is not valid")

        nodes_i = self.sequences_to_list(nodes_sequence_i)
        nodes_r = self.sequences_to_list(nodes_sequence_r)
        stops_i = self.sequences_to_list(stops_sequence_i)
        stops_r = self.sequences_to_list(stops_sequence_r)

        if self.direction_validator(nodes_i, nodes_r):
            if self.stops_validator(nodes_i, stops_i) and self.stops_validator(nodes_r, stops_r):
                if self.sequences_validator(nodes_i) and self.sequences_validator(nodes_r):
                    return True

    @staticmethod
    def sequences_to_string(sequence_list):
        """
        to get a string with a sequences list
        :param sequence_list:
        :return:
        """
        line = ""
        for node in sequence_list:
            if line == "":
                line = line + node
            else:
                line = line + "," + node
        return line

    @staticmethod
    def sequences_to_list(sequence):
        """
        to get a list with a sequence string
        :param sequence:
        :return:
        """
        if sequence == "":
            return []

        nodes = sequence.split(",")

        for node in nodes:
            i = nodes.index(node)
            nodes[i] = node.rstrip("\n")

        return nodes

    @staticmethod
    def stops_validator(nodes_list, stops_list):
        """
        to check if all stops of a direction of a route are a sub group of node_sequences. Also check if first and last
        nodes are stops
        :param nodes_list:
        :param stops_list:
        :return:
        """
        # to check if each stops be in node_sequences
        for stop in stops_list:
            if stop not in nodes_list:
                raise StopsSequencesException("stop is not reachable")
        # to check if first stop is equal to first node in node sequences
        if nodes_list[0] != stops_list[0]:
            raise FirstStopIsNotValidException("first stop is not valid, must be equal to first node")
        # to check if last stop is equal to last node in node sequences
        if nodes_list[len(nodes_list) - 1] != stops_list[len(stops_list) - 1]:
            raise LastStopIsNotValidException("last stop is not valid, must be equal to last node")
        return True

    @staticmethod
    def direction_validator(nodes_list_i, nodes_list_r):
        """
        to check if both direction of a route form a cycle
        :param nodes_list_i:
        :param nodes_list_r:
        :return:
        """
        if nodes_list_i[0] != nodes_list_r[len(nodes_list_r) - 1] or \
                nodes_list_r[0] != nodes_list_i[len(nodes_list_i) - 1]:
            raise NotCycleException("sequence of nodes of both directions do not form a cycle")
        return True

    @staticmethod
    def sequences_validator(sequence):

        for node1 in sequence:
            n = 0
            for node2 in sequence:
                if node1 == node2:
                    n = n + 1
            if n > 1:
                raise NodeSequencesIsNotValidException("node sequence loops")

        return True


class TransportNetwork:

    def __init__(self, graph_obj):
        self.__graph_obj = graph_obj
        self.__routes = []
        self.__routes_id = []

    def __edges_validator(self, node_list):
        """
        to check if each edges in a node_sequences exist in the graph object
        :param node_list:
        :return:
        """
        for i in range(len(node_list) - 1):
            j = i + 1
            if not self.__graph_obj.edge_exist(node_list[i], node_list[j]):
                raise NodeSequencesIsNotValidException("Node sequences is not valid because a edge does not exist")
        return True

    def is_valid(self):
        """
        to check if Transport Network is valid
        :return:
        """
        # could be added a validation of whether the defined routes are specific to transport the defined demand,
        # very difficult to do
        if len(self.__routes) == 0:
            return False
        else:
            return True

    def get_routes(self):
        """
        to get all routes
        :return:
        """
        return self.__routes

    def get_route(self, route_id):
        """
        to get a specific route with a route_id
        :param route_id:
        :return:
        """
        if route_id in self.__routes_id:
            i = self.__routes_id.index(route_id)
            return self.__routes[i]
        else:
            raise RouteIdNotFoundException("route_id not found")

    def add_route(self, route_obj):
        """
        to add a specific route in routes list
        :param route_obj:
        :return:
        """
        if not isinstance(route_obj, Route):
            raise RouteIsNotvalidException("route_obj is not valid")

        route_id = route_obj.id
        nodes_sequence_i = route_obj.nodes_sequence_i
        nodes_sequence_r = route_obj.nodes_sequence_r

        if self.__edges_validator(nodes_sequence_i) or self.__edges_validator(nodes_sequence_r):
            if route_id not in self.__routes_id:
                self.__routes.append(route_obj)
                self.__routes_id.append(route_id)
            else:
                raise RouteIdDuplicatedException("route_id is duplicated")

    def delete_route(self, route_id):
        """
        to delete a specific route_id in list of routes
        :param route_id:
        :return:
        """
        if route_id in self.__routes_id:
            i = self.__routes_id.index(route_id)
            self.__routes_id.pop(i)
            self.__routes.pop(i)
        else:
            raise RouteIdNotFoundException("route_id not found")

    def routes_to_file(self, file_path):
        """
        to save file with all routes information
        :param file_path:
        :return:
        """
        # route_id, mode_name, nodes_sequence_i, nodes_sequence_r, stops_sequence_i, stops_sequence_r
        col_route_id = []
        col_mode = []
        col_nodes_sequence_i = []
        col_nodes_sequence_r = []
        col_stops_sequence_i = []
        col_stops_sequence_r = []

        for route in self.__routes:
            col_route_id.append(route.id)
            col_mode.append(route.mode.name)
            col_nodes_sequence_i.append(route.sequences_to_string(route.nodes_sequence_i))
            col_nodes_sequence_r.append(route.sequences_to_string(route.nodes_sequence_r))
            col_stops_sequence_i.append(route.sequences_to_string(route.stops_sequence_i))
            col_stops_sequence_r.append(route.sequences_to_string(route.stops_sequence_r))

        df_transit_network = pd.DataFrame()
        df_transit_network["route_id"] = col_route_id
        df_transit_network["mode"] = col_mode
        df_transit_network["nodes_sequence_i"] = col_nodes_sequence_i
        df_transit_network["nodes_sequence_r"] = col_nodes_sequence_r
        df_transit_network["stops_sequence_i"] = col_stops_sequence_i
        df_transit_network["stops_sequence_r"] = col_stops_sequence_r

        df_transit_network.to_csv(file_path, sep=";", index=False)

    def get_circular_routes(self, mode_obj):
        """
        to add predefined circular routes, 2 routes with only a direction and whose stops and nodes sequence are all
        subcenter nodes.
        :param mode_obj:
        :return: None
        """

        zones = self.__graph_obj.get_zones()
        if len(zones) <= 1:
            raise CircularRouteIsNotValidException("to add a predefined circular route you have a city "
                                                   "with more of one zone created")

        if not isinstance(mode_obj, TransportMode):
            raise ModeIsNotValidException("mode obj is not valid")

        mode_name = mode_obj.name

        route_id_i = "CIR_I_{}".format(mode_name)
        route_id_r = "CIR_R_{}".format(mode_name)

        nodes_sequence_i = ""
        nodes_sequence_r = ""

        for i in range(len(zones)):

            if nodes_sequence_i == "":
                nodes_sequence_i = nodes_sequence_i + str(zones[i].subcenter.id)
                nodes_sequence_r = nodes_sequence_r + str(zones[len(zones) - 1 - i].subcenter.id)
            else:
                nodes_sequence_i = nodes_sequence_i + "," + str(zones[i].subcenter.id)
                nodes_sequence_r = nodes_sequence_r + "," + str(zones[len(zones) - 1 - i].subcenter.id)

        nodes_sequence_i = nodes_sequence_i + "," + str(zones[0].subcenter.id)
        nodes_sequence_r = nodes_sequence_r + "," + str(zones[len(zones) - 1].subcenter.id)

        stops_sequence_i = nodes_sequence_i
        stops_sequence_r = nodes_sequence_r

        route1 = Route(route_id_i, mode_obj, nodes_sequence_i, "", stops_sequence_i, "", _type=RouteType.PREDEFINED)
        route2 = Route(route_id_r, mode_obj, "", nodes_sequence_r, "", stops_sequence_r, _type=RouteType.PREDEFINED)

        return [route1, route2]

    def get_feeder_routes(self, mode_obj):
        """
        to add predefined feeder routes, where for each zone exist a route with nodes and stops sequences beetween
        p-sc for I direction and sc-p for R direction.
        :param mode_obj: name of mode of the all feeder routes
        :return: None
        """

        if not isinstance(mode_obj, TransportMode):
            raise ModeIsNotValidException("mode obj is not valid")

        mode_name = mode_obj.name

        routes = []
        for zone in self.__graph_obj.get_zones():
            id_p = zone.periphery.id
            id_sc = zone.subcenter.id

            route_id = "F_{}_{}".format(mode_name, zone.id)
            nodes_sequence_i = "{},{}".format(id_p, id_sc)
            stops_sequence_i = nodes_sequence_i
            nodes_sequence_r = "{},{}".format(id_sc, id_p)
            stops_sequence_r = nodes_sequence_r

            route = Route(route_id, mode_obj, nodes_sequence_i, nodes_sequence_r, stops_sequence_i,
                          stops_sequence_r, _type=RouteType.PREDEFINED)

            routes.append(route)

        return routes

    def get_radial_routes(self, mode_obj, short=False, express=False):
        """
        to add predefined radial routes, where for each zone exist a route with nodes and stops sequences beetween
        p-sc-cbd for I direction and cbd-sc-p for R direction.
        :param mode_obj: name of mode of the all radial routes
        :param short: if radial routes omit the passage through the periphery (default: False)
        :param express: if radial routes omit to stop in the subcenter (default: False)
        :return: None
        """

        if not isinstance(mode_obj, TransportMode):
            raise ModeIsNotValidException("mode obj is not valid")

        mode_name = mode_obj.name

        cbd = self.__graph_obj.get_cbd()
        id_cbd = cbd.id

        routes = []

        for zone in self.__graph_obj.get_zones():

            id_p = zone.periphery.id
            id_sc = zone.subcenter.id

            if short is True:
                route_id = "RS_{}_{}".format(mode_name, zone.id)
                nodes_sequence_i = "{},{}".format(id_sc, id_cbd)
                stops_sequence_i = nodes_sequence_i
                nodes_sequence_r = "{},{}".format(id_cbd, id_sc)
                stops_sequence_r = nodes_sequence_r
            else:
                if express is True:
                    route_id = "RE_{}_{}".format(mode_name, zone.id)
                    nodes_sequence_i = "{},{},{}".format(id_p, id_sc, id_cbd)
                    stops_sequence_i = "{},{}".format(id_p, id_cbd)
                    nodes_sequence_r = "{},{},{}".format(id_cbd, id_sc, id_p)
                    stops_sequence_r = "{},{}".format(id_cbd, id_p)
                else:
                    route_id = "R_{}_{}".format(mode_name, zone.id)
                    nodes_sequence_i = "{},{},{}".format(id_p, id_sc, id_cbd)
                    stops_sequence_i = nodes_sequence_i
                    nodes_sequence_r = "{},{},{}".format(id_cbd, id_sc, id_p)
                    stops_sequence_r = nodes_sequence_r

            route = Route(route_id, mode_obj, nodes_sequence_i, nodes_sequence_r, stops_sequence_i,
                          stops_sequence_r, _type=RouteType.PREDEFINED)
            routes.append(route)

        return routes

    def get_diametral_routes(self, mode_obj, jump, short=False, express=False):
        """
        to add predefined diametral routes, where for each zone exist a route with nodes and stops sequences beetween
        p-sc-cbd-sc'-p' for I direction and p'-sc'-cbd-sc-p for R direction. p' and sc' are periphery and subcenter
        nodes with zone id equivalent to the id of the treated zone plus the jump
        :param mode_obj: name of mode of the all diametral routes
        :param jump: to identified other zone where diametral routes transit
        :param short: if diametral routes omit the passage through the periphery (default: False)
        :param express: if diametral routes omit to stop in the subcenter and cbd nodes  (default: False)
        :return: None
        """
        if not isinstance(mode_obj, TransportMode):
            raise ModeIsNotValidException("mode obj is not valid")

        mode_name = mode_obj.name

        cbd = self.__graph_obj.get_cbd()
        id_cbd = cbd.id

        zones = self.__graph_obj.get_zones()
        if jump >= len(zones) or jump <= 0 or not isinstance(jump, int):
            raise JumpIsNotValidException("jump must be a int in range (0-n° zones)")

        routes = []

        for zone in zones:
            id_p = zone.periphery.id
            id_sc = zone.subcenter.id

            zone_id = zone.id

            if zone_id + jump <= len(zones):
                zone2_id = zone_id + jump
            else:
                zone2_id = zone_id + jump - len(zones)

            # zones are sort per id in list
            zone2 = zones[zone2_id - 1]

            id_p2 = zone2.periphery.id
            id_sc2 = zone2.subcenter.id

            if short is True:
                if express is True:
                    route_id = "DSE{}_{}_{}".format(jump, mode_name, zone.id)
                    nodes_sequence_i = "{},{},{}".format(id_sc, id_cbd, id_sc2)
                    stops_sequence_i = "{},{}".format(id_sc, id_sc2)
                    nodes_sequence_r = "{},{},{}".format(id_sc2, id_cbd, id_sc)
                    stops_sequence_r = "{},{}".format(id_sc2, id_sc)
                else:
                    route_id = "DS{}_{}_{}".format(jump, mode_name, zone.id)
                    nodes_sequence_i = "{},{},{}".format(id_sc, id_cbd, id_sc2)
                    stops_sequence_i = nodes_sequence_i
                    nodes_sequence_r = "{},{},{}".format(id_sc2, id_cbd, id_sc)
                    stops_sequence_r = nodes_sequence_r
            else:
                if express is True:
                    route_id = "DE{}_{}_{}".format(jump, mode_name, zone.id)
                    nodes_sequence_i = "{},{},{},{},{}".format(id_p, id_sc, id_cbd, id_sc2, id_p2)
                    stops_sequence_i = "{},{}".format(id_p, id_p2)
                    nodes_sequence_r = "{},{},{},{},{}".format(id_p2, id_sc2, id_cbd, id_sc, id_p)
                    stops_sequence_r = "{},{}".format(id_p2, id_p)
                else:
                    route_id = "D{}_{}_{}".format(jump, mode_name, zone.id)
                    nodes_sequence_i = "{},{},{},{},{}".format(id_p, id_sc, id_cbd, id_sc2, id_p2)
                    stops_sequence_i = nodes_sequence_i
                    nodes_sequence_r = "{},{},{},{},{}".format(id_p2, id_sc2, id_cbd, id_sc, id_p)
                    stops_sequence_r = nodes_sequence_r
            route = Route(route_id, mode_obj, nodes_sequence_i, nodes_sequence_r, stops_sequence_i,
                          stops_sequence_r, _type=RouteType.PREDEFINED)
            routes.append(route)

        return routes

    def get_tangencial_routes(self, mode_obj, jump, short=False, express=False):
        """
        to add predefined tangencial routes, where for each zone exist a route with nodes and stops sequences beetween
        p-sc-sc'-...-sc''-p'' for I direction and p''-sc''-...-sc'-sc-p for R direction. sc', ..., sc'' are subcenter
        nodes with zone id less than or equal to id of the treated zone plus the jump. p'' and sc'' are periphery
        and subcenter nodes with id equivalent to the id of the treated zone plus the jump
        :param mode_obj: name of mode of the all tangencial routes
        :param jump: to identified other zone where tangencial routes transit
        :param short: if radial routes omit the passage through the periphery (default: False)
        :param express: if radial routes omit to stop in the subcenters nodes (default: False)
        :return: None
        """
        if not isinstance(mode_obj, TransportMode):
            raise ModeIsNotValidException("mode obj is not valid")

        mode_name = mode_obj.name

        zones = self.__graph_obj.get_zones()
        if jump >= len(zones) or jump <= 0 or not isinstance(jump, int):
            raise JumpIsNotValidException("jump must be a int in range (0-n° zones)")

        routes = []

        for zone in zones:
            id_p = zone.periphery.id
            id_sc = zone.subcenter.id

            zone_id = zone.id

            if zone_id + jump <= len(zones):
                zone2_id = zone_id + jump
            else:
                zone2_id = zone_id + jump - len(zones)

            # zones are sort per id in list
            zone2 = zones[zone2_id - 1]

            id_p2 = zone2.periphery.id
            id_sc2 = zone2.subcenter.id

            list_zones_id = []

            if zone2_id > zone_id and jump != 1:
                for i in range(zone_id + 1, zone2_id):
                    list_zones_id.append(i)

            if zone2_id < zone_id:
                if zone_id != len(zones):
                    for i in range(zone_id + 1, len(zones) + 1):
                        list_zones_id.append(i)

                for i in range(1, zone2_id):
                    list_zones_id.append(i)

            if short is True:
                if express is True:
                    route_id = "TSE{}_{}_{}".format(jump, mode_name, zone.id)

                    nodes_sequence_i = "{}".format(id_sc)
                    nodes_sequence_r = "{}".format(id_sc2)

                    for i in range(len(list_zones_id)):
                        zone3 = zones[list_zones_id[i] - 1]
                        zone4 = zones[list_zones_id[len(list_zones_id) - 1 - i] - 1]

                        nodes_sequence_i = nodes_sequence_i + "," + str(zone3.subcenter.id)
                        nodes_sequence_r = nodes_sequence_r + "," + str(zone4.subcenter.id)

                    nodes_sequence_i = nodes_sequence_i + "," + str("{}".format(id_sc2))
                    nodes_sequence_r = nodes_sequence_r + "," + str("{}".format(id_sc))

                    stops_sequence_i = "{},{}".format(id_sc, id_sc2)
                    stops_sequence_r = "{},{}".format(id_sc2, id_sc)

                else:
                    route_id = "TS{}_{}_{}".format(jump, mode_name, zone.id)
                    nodes_sequence_i = "{}".format(id_sc)
                    nodes_sequence_r = "{}".format(id_sc2)
                    for i in range(len(list_zones_id)):
                        zone3 = zones[list_zones_id[i] - 1]
                        zone4 = zones[list_zones_id[len(list_zones_id) - 1 - i] - 1]

                        nodes_sequence_i = nodes_sequence_i + "," + str(zone3.subcenter.id)
                        nodes_sequence_r = nodes_sequence_r + "," + str(zone4.subcenter.id)
                    nodes_sequence_i = nodes_sequence_i + "," + "{}".format(id_sc2)
                    nodes_sequence_r = nodes_sequence_r + "," + "{}".format(id_sc)
                    stops_sequence_i = nodes_sequence_i
                    stops_sequence_r = nodes_sequence_r

            else:
                if express is True:
                    route_id = "TE{}_{}_{}".format(jump, mode_name, zone.id)
                    nodes_sequence_i = "{},{}".format(id_p, id_sc)
                    nodes_sequence_r = "{},{}".format(id_p2, id_sc2)
                    for i in range(len(list_zones_id)):
                        zone3 = zones[list_zones_id[i] - 1]
                        zone4 = zones[list_zones_id[len(list_zones_id) - 1 - i] - 1]

                        nodes_sequence_i = nodes_sequence_i + "," + str(zone3.subcenter.id)
                        nodes_sequence_r = nodes_sequence_r + "," + str(zone4.subcenter.id)
                    nodes_sequence_i = nodes_sequence_i + "," + "{},{}".format(id_sc2, id_p2)
                    nodes_sequence_r = nodes_sequence_r + "," + "{},{}".format(id_sc, id_p)
                    stops_sequence_i = "{},{}".format(id_p, id_p2)
                    stops_sequence_r = "{},{}".format(id_p2, id_p)
                else:
                    route_id = "T{}_{}_{}".format(jump, mode_name, zone.id)
                    nodes_sequence_i = "{},{}".format(id_p, id_sc)
                    nodes_sequence_r = "{},{}".format(id_p2, id_sc2)
                    for i in range(len(list_zones_id)):
                        zone3 = zones[list_zones_id[i] - 1]
                        zone4 = zones[list_zones_id[len(list_zones_id) - 1 - i] - 1]

                        nodes_sequence_i = nodes_sequence_i + "," + str(zone3.subcenter.id)
                        nodes_sequence_r = nodes_sequence_r + "," + str(zone4.subcenter.id)
                    nodes_sequence_i = nodes_sequence_i + "," + "{},{}".format(id_sc2, id_p2)
                    nodes_sequence_r = nodes_sequence_r + "," + "{},{}".format(id_sc, id_p)
                    stops_sequence_i = nodes_sequence_i
                    stops_sequence_r = nodes_sequence_r

            route = Route(route_id, mode_obj, nodes_sequence_i, nodes_sequence_r, stops_sequence_i,
                          stops_sequence_r, _type=RouteType.PREDEFINED)
            routes.append(route)

        return routes

    def update_route(self, route_id, **kwargs):
        """
        to update route information
        :param route_id:
        :return:
        """
        if route_id not in self.__routes_id:
            raise RouteIdNotFoundException("route_id does not exist")

        i = self.__routes_id.index(route_id)
        route_obj = self.__routes[i]
        for attr in kwargs:
            setattr(route_obj, attr, kwargs[attr])

    def plot(self, file_path, list_routes=None):
        """
        to plot graph
        :return:
        """
        # if list routes is empty then plot all routes
        if list_routes is None:
            list_routes = self.__routes_id

        # edges information and positions
        # edge city
        edges_graph = []
        position = defaultdict(list)
        for edge in self.__graph_obj.get_edges():
            edges_graph.append((str(edge.node1.id), str(edge.node2.id)))
            if not position.get(str(edge.node1.id)):
                position[str(edge.node1.id)].append(edge.node1.x)
                position[str(edge.node1.id)].append(edge.node1.y)
            if not position.get(str(edge.node2.id)):
                position[str(edge.node2.id)].append(edge.node2.x)
                position[str(edge.node2.id)].append(edge.node2.y)

        # nodes information and positions
        info_cbd = []
        info_sc = []
        info_p = []
        id_cbd = []
        id_sc = []
        id_p = []
        x_cbd = []
        y_cbd = []
        x_sc = []
        y_sc = []
        x_p = []
        y_p = []

        for node in self.__graph_obj.get_nodes():
            if isinstance(node, graph.CBD):
                info_cbd.append(node)
            if isinstance(node, graph.Periphery):
                info_p.append(node)
            if isinstance(node, graph.Subcenter):
                info_sc.append(node)

        for cbd in info_cbd:
            x_cbd.append(cbd.x)
            y_cbd.append(cbd.y)
            id_cbd.append(str(cbd.id))

        for sc in info_sc:
            x_sc.append(sc.x)
            y_sc.append(sc.y)
            id_sc.append(str(sc.id))
        for p in info_p:
            x_p.append(p.x)
            y_p.append(p.y)
            id_p.append(str(p.id))

        # edges routes and stops
        edges_i = []
        edges_r = []
        stops = []
        for route_id in list_routes:
            if route_id not in self.__routes_id:
                raise RouteIdNotFoundException("route_id does not found")
            else:
                ind = self.__routes_id.index(route_id)
                route = self.__routes[ind]
                nodes_i = route.nodes_sequence_i
                nodes_r = route.nodes_sequence_r
                stops_i = route.stops_sequence_i
                stops_r = route.stops_sequence_r

                for i in range(len(nodes_i) - 1):
                    id1 = nodes_i[i]
                    id2 = nodes_i[i + 1]
                    edges_i.append((id1, id2))
                for i in range(len(nodes_r) - 1):
                    id1 = nodes_r[i]
                    id2 = nodes_r[i + 1]
                    edges_r.append((id1, id2))
                for i in range(len(stops_i)):
                    if stops_i[i] not in stops:
                        stops.append(stops_i[i])
                for i in range(len(stops_r)):
                    if stops_r[i] not in stops:
                        stops.append(stops_r[i])

        G = nx.DiGraph()
        G.add_edges_from(edges_graph)
        G.add_edges_from(edges_i)
        G.add_edges_from(edges_r)

        # separate calls to draw labels, nodes and edges
        # plot p, Sc and CBD
        nx.draw_networkx_nodes(G, position, cmap=plt.get_cmap('Set2'), nodelist=id_p, node_color='red', node_size=300)
        nx.draw_networkx_nodes(G, position, cmap=plt.get_cmap('Set2'), nodelist=id_sc, node_color='blue', node_size=300)
        nx.draw_networkx_nodes(G, position, cmap=plt.get_cmap('Set2'), nodelist=id_cbd, node_color='purple',
                               node_size=300)
        # plot stops
        nx.draw_networkx_nodes(G, position, cmap=plt.get_cmap('Set2'), nodelist=stops, node_color='yellow',
                               node_size=300)
        # plot labels
        nx.draw_networkx_labels(G, position)
        # plot edges city
        nx.draw_networkx_edges(G, position, edgelist=edges_graph, edge_color='orange', arrows=True)
        # plot edges_i
        nx.draw_networkx_edges(G, position, edgelist=edges_i, edge_color='lime', arrows=True)
        # plot edges_r
        nx.draw_networkx_edges(G, position, edgelist=edges_r, edge_color='aqua', arrows=True)

        plt.title("City graph")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.gca().set_aspect('equal')
        plt.savefig(file_path)
