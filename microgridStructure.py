from microgrid_Model import *
import networkx as nx
from scipy.sparse import dok_matrix
'''Initialize a special case of microgrid'''
class MicrogridCase_Simple:
    def __init__(self,device,NumOfTime,graph=None):
        self.device = device
        self.type = 'Simple'
        self.NumOfTime = NumOfTime
    def getKey(self,type):
        return [key for key in self.device.keys() if isinstance(self.device[key], type)]
    def SOCUpdate(self, plan, nowtime):
        N_es = self.getKey(electricStorage)
        for es in N_es:
            self.device[es].SOCnow = plan[es + '电池电量'].loc[nowtime] / self.device[es].capacity
class MicrogridCase_Graph:
    def __init__(self,graph,NumOfTime):
        ns = graph.nodes()
        for i in range(len(ns)):
            graph.node[ns[i]].update({'index':i})
        self.graph = graph
        device = dict()
        for node in graph.nodes():
            device.update(graph.node[node]['device'])
        self.device = device
        self.type = 'Graph'
        self.NumOfTime = NumOfTime
        self.Adj = nx.adjacency_matrix(graph)
        ns = graph.nodes()
        B = dok_matrix((len(ns),len(ns)))
        for l in graph.edges():
            i = graph.node[l[0]]['index']
            j = graph.node[l[1]]['index']
            B[i,j] = - 1/graph.edge[l[0]][l[1]]['X']
        B = B + B.transpose()
        for i in range(len(ns)):
            B[i,i] = - sum(B[i,j] for j in range(len(ns)))
        self.B = B
    def getKey(self, type):
        return [key for key in self.device.keys() if isinstance(self.device[key], type)]


device_IES = {
    'PV_1' : PV(),
    'ES_1' : electricStorage(),
    'ABSC_1' : absorptionChiller(),
    'BOL_1' : boiler(),
    'CS_1' : coldStorage(),
    'AC_1' : airConditioner(),
    'GT_1' : gasTurbine(),
    'DR_Heat_Load' : DRHeatLoad(),
    'ut' : utility(),
    'inv' : inverter()
}
case_IES = MicrogridCase_Simple(device=device_IES, NumOfTime=96)
graph_PS = nx.Graph()
graph_PS.add_nodes_from(['A','B','C','D','E'])
graph_PS.add_edges_from([('A','B'),('A','E'),('B','C'),('C','D'),('D','E'),('A','D')])
graph_PS.node['A'].update({
    'ID' : 'A',
    'device' : {
        'Park City' : gasTurbine(Pmax=170,Pmin=10,Cost=15),
        'Alta' : PV()
    }
})
graph_PS.node['B'].update({
    'ID' : 'B',
    'device': {}
    })
graph_PS.node['C'].update({
    'ID' : 'C',
    'device':{
        'Solitude' : gasTurbine(Pmax=320,Pmin=10,Cost=30)
    }
})
graph_PS.node['D'].update({
    'ID' : 'D',
    'device':{
        'Sundance' : gasTurbine(Pmax=200,Pmin=10,Cost=40)
    }
})
graph_PS.node['E'].update({
    'ID' : 'E',
    'device':{
        'Brighton':gasTurbine(Pmax=600,Pmin=10,Cost=20)
    }
})
graph_PS.edge['A']['B'].update({
    'R' : 0.281,
    'X' : 2.81,
    'Limit' : 400
})
graph_PS.edge['A']['D'].update({
    'R' : 0.304,
    'X' : 3.04,
    'Limit' : None
})
graph_PS.edge['A']['E'].update({
    'R' : 0.064,
    'X' : 0.64,
    'Limit' : None
})
graph_PS.edge['B']['C'].update({
    'R' : 0.108,
    'X' : 1.08,
    'Limit' : None
})
graph_PS.edge['C']['D'].update({
    'R' : 0.297,
    'X' : 2.97,
    'Limit' : None
})
graph_PS.edge['D']['E'].update({
    'R' : 0.297,
    'X' : 2.97,
    'Limit' : 240
})
case_PS = MicrogridCase_Graph(graph=graph_PS,NumOfTime=96)