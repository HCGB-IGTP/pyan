#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Graph markup writers."""

import sys
import logging
import time
import re

class Writer(object):
    def __init__(self, graph, output=None, logger=None, child_option=False, tabstop=4, focus=None):
        self.graph = graph
        self.output = output
        self.logger = logger or logging.getLogger(__name__)
        self.indent_level = 0
        self.tabstop = tabstop*' '
        
        # added
        self.focus = focus
        self.child_option = child_option

    def log(self, msg):
        self.logger.info(msg)

    def indent(self, level=1):
        self.indent_level += level

    def dedent(self, level=1):
        self.indent_level -= level

    def write(self, line):
        self.outstream.write(self.tabstop*self.indent_level+line+'\n')

    def run(self):
        self.log('%s running' % type(self))
        try:
            self.outstream = open(self.output, 'w')
        except TypeError:
            self.outstream = sys.stdout
        self.start_graph()
        (edges2include, nodes2include) = self.check_graph(self.focus, self.child_option)
        
        #print ("edges2include: ")
        #print (edges2include)
        #print ("nodes2include: ")
        #print (nodes2include)
        #exit()
        
        self.write_subgraph(self.graph, nodes2include, edges2include)
        self.write_edges(edges2include)
        self.finish_graph()
        if self.output:
            self.outstream.close()

    def write_subgraph(self, graph, nodes2include, edges2include):
        returned = self.start_subgraph(graph, nodes2include, edges2include)
        if (returned):                
            for node in graph.nodes:
                self.write_node(node, edges2include)
            for subgraph in graph.subgraphs:
                self.write_subgraph(subgraph, nodes2include, edges2include)
            
            self.finish_subgraph(graph)

    def write_edges(self, edges2include):
        self.start_edges()
        for edge in self.graph.edges:
            self.write_edge(edge, edges2include)
        self.finish_edges()

    def start_graph(self):
        pass

    def start_subgraph(self, graph, nodes2include, egdes2include):
        pass

    def write_node(self, node):
        pass

    def start_edges(self):
        pass

    def write_edge(self, edge):
        pass

    def finish_edges(self):
        pass

    def finish_subgraph(self, graph):
        pass

    def finish_graph(self):
        pass

class DotWriter(Writer):
    def __init__(self, graph,
                 options=None, output=None, logger=None, tabstop=4, child_option=False, focus=None):
        Writer.__init__(
                self, graph,
                output=output,
                logger=logger,
                focus=focus,
                child_option=child_option,
                tabstop=tabstop)
        options = options or []
        if graph.grouped:
            options += ['clusterrank="local"']
        self.options = ', '.join(options)
        self.grouped = graph.grouped

    def start_graph(self):
        self.write('digraph G {')
        self.write('    graph [' + self.options + '];')
        self.indent()

    def check_graph(self, focus, child_option):
        edges2include = []
        regex_pattern = r".*" + re.escape(focus) + r".+"
        
        for edge in self.graph.edges:
            source = edge.source
            target = edge.target
            color  = edge.color
            
            #print ("#####")
            #print ("source: ", source.id)
            #print ("target: ", target.id)
            
            if (re.match(regex_pattern, source.id) or 
                re.match(regex_pattern, target.id)):
                
                if child_option:
                    if (re.match(regex_pattern, source.id)):
                        edges2include.append(target.id)
                        #print ("** add target **") 
                else:
                    edges2include.append(source.id)
                    edges2include.append(target.id)
                    #print ("** add BOTH **")

        edges2include = list(set(edges2include))
        
        nodes2include = []
        for e in edges2include:
            nodes2include.append('__'.join(e.split('__')[:-1]))
        
        ## include nodes not visited by any other
        unique_nodes2include = [] 
        for subgraph in self.graph.subgraphs:
            for node in subgraph.nodes:
                if (re.match(regex_pattern, node.id)):
                    unique_nodes2include.append(node.id)
        
        #print (unique_nodes2include)
        
        unique_edges2include = []
        for edge in self.graph.edges:
            source = edge.source
            target = edge.target
            color  = edge.color
            
            if (source.id in unique_nodes2include):
                unique_edges2include.append(source.id)
            
        
        nodes2include = nodes2include + unique_nodes2include
        nodes2include = list(set(nodes2include))
        
        edges2include = edges2include + unique_edges2include
        edges2include = list(set(edges2include))
        return (edges2include, nodes2include) 
    
    def start_subgraph(self, graph, nodes2include, edges2include):
        if (graph.id == 'G' or graph.id in nodes2include):
             #print ("Subgraph id: ", graph.id    )
            #print ("Subgraph label: ", graph.label)
                
            self.log('Start subgraph %s' % graph.label)
            # Name must begin with "cluster" to be recognized as a cluster by GraphViz.
            self.write("subgraph cluster_%s {\n" % graph.id)
            self.indent()
    
            # translucent gray (no hue to avoid visual confusion with any
            # group of colored nodes)
            self.write('graph [style="filled,rounded",fillcolor="#80808018", label="%s"];' % graph.label)
            return (1)
        else:
            return (0)

    def finish_subgraph(self, graph):
        self.log('Finish subgraph %s' % graph.label)
        # terminate previous subgraph
        self.dedent()
        self.write('}')

    def write_node(self, node, focus):
        #print ("Node id: ", node.id    )
        #print ("Node label: ", node.label)
        #time.sleep(1)
        if (node.id in focus):
            self.log('Write node %s' % node.label)
            self.write('%s [label="%s", style="filled", fillcolor="%s", fontcolor="%s", group="%s"];'
                % (node.id, node.label, node.fill_color, node.text_color, node.group))
            
            return (1)
        else:
            return (0)

    def write_edge(self, edge, edges2include):
        source = edge.source
        target = edge.target
        color  = edge.color
        
        if (source.id in edges2include and target.id in edges2include):
            
            if edge.flavor == 'defines':
                self.write('    %s -> %s [style="dashed", color="%s"];'
                    % (source.id, target.id, color))
            else: # edge.flavor == 'uses':
                self.write('    %s -> %s [style="solid", color="%s"];'
                    % (source.id, target.id, color))
            return (1)
        else:
            return (0)

    def finish_graph(self):
        self.write('}')  # terminate "digraph G {"
