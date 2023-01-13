
import my_modules .my_tracing as debugging

class Graph:
    def __init__ (self):
        debugging .log ("Initializing graph")
        self .vertex_set = None
        self .edge_set = None
        self .adjacency_matrix = None
        self .capacity_matrix = None

    @debugging .trace (level = 2)
    def add_vertex_set (self, vertex_set):
        self .vertex_set = vertex_set

    @debugging .trace (level = 2)
    def add_edge_set (self, edge_set): #edges with form (source_vertex, destination_vertex, capacity)
        self .edge_set = edge_set

    @debugging .trace (level = 2)
    def vertices (self):
        for v in self .vertex_set :
            yield v
    
    @debugging .trace (level = 2)
    def size (self):
        return len (self .vertex_set)

    @debugging .trace (level = 2)
    def build_flow_network (self):
        if self .vertex_set and self .edge_set : 
            #self .adjacency_matrix = {u : {v : False for v in self .vertices ()} for u in self .vertices ()}
            self .capacity_matrix = {u : {v : 0 for v in self .vertices ()} for u in self .vertices ()}
            for (u, v, c) in self .edge_set:
                #self .adjacency_matrix [u] [v] = True
                self .capacity_matrix [u] [v] = c
        else :
            raise Exception ("Provide edge and vertex sets")

    @debugging .trace (level = 2)
    def is_adjacent (self, u, v) :
        return self .capacity_matrix [u] [v] > 0
    
    @debugging .trace (level = 2)
    def get_capacity (self, u, v) :
        return self .capacity_matrix [u] [v]

    def reduce_capacity (self, u, v, c) :
        self .capacity_matrix [u] [v] -= c



class FordFulkersonAlgorithm :
    def __init__ (self, V, E):
        debugging .log ("Initializing Ford Fulkerson Algorithm")
        self .g = Graph ()
        self .g .add_vertex_set (V)
        self .g .add_edge_set (E)
        self .g .build_flow_network ()
        self .max_flow_graph = {}

    @debugging .trace (level = 2)
    def BFS (self, s, t, parent):
        visited = {v : False for v in self .g .vertices ()}
        queue = []
        
        queue .append (s)
        visited [s] = True

        while queue:
            u = queue .pop (0)
            for v in self .g .vertices ():
                if not visited [v] and self .g .is_adjacent (u, v) :
                    queue .append (v)
                    visited [v] = True
                    parent [v] = u

        return visited [t]

    @debugging .trace (level = 1)
    def run (self, source = 'S', sink = 'T') :
        parent = {v : -1 for v in self .g .vertices ()}
        max_flow = 0
        path_flow = float("Inf")

        while self .BFS (source, sink, parent) :
            s = sink
            while s != source :
                path_flow = min (path_flow, self .g .get_capacity (parent [s], s))
                debugging .log (s, '<--', end = '')
                s = parent [s]
            debugging .log (source, "; flow val", path_flow)
            max_flow += path_flow

            v = sink
            while v!= source :
                u = parent [v]
                self .g .reduce_capacity (u, v, path_flow)
                if (u,v) not in self .max_flow_graph :
                    self .max_flow_graph [(u ,v)] = path_flow
                else :
                    self .max_flow_graph [(u, v)] += path_flow
                v = parent [v]

            path_flow = float("Inf")

        debugging .log ("Max flow value", max_flow)
        debugging .log ("Max flow graph", self .max_flow_graph)
        return max_flow, self .max_flow_graph



class EdmondsKarpAlgorithm :
    def __init__ (self):
        pass

if __name__ == '__main__' :
    V = ['S', 1, 2, 3, 4, 'T']
    E = [('S', 1, 16), ('S', 2, 13), (1, 2, 10), (1, 3, 12), (2, 1, 4), (2, 4, 14), (3, 2, 9), (3, 'T', 20), (4, 3, 7),
            (4, 'T', 4)]
    f = FordFulkersonAlgorithm (V, E)
    mf_val, mf_graph = f .run ()
