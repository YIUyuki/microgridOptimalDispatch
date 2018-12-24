from microgrid_Model import *
import networkx as nx
'''Initialize a special case of microgrid'''
#from neo4j.v1 import GraphDatabase

#driver = GraphDatabase.driver("bolt://localhost:7687", auth=("zidanessf", "123456"))
#graph = nx.Graph()
def get_node(tx, name, graph):
    return tx.run("MATCH (n:$name) RETURN n",name = name)


def get_branch(tx, name):
    for record in tx.run("MATCH (a:Person)-[:KNOWS]->(friend) WHERE a.name = $name "
                         "RETURN friend.name ORDER BY friend.name", name=name):
        print(record["friend.name"])

class MicrogridCase:
    def __init__(self):
        microgrid_device = dict()
        microgrid_device['PV_1'] = PV()
        microgrid_device['ES_1'] = electricStorage(capacity=3600,Pmax_in=600)
        microgrid_device['ES_2'] = electricStorage(capacity=3600,Pmax_in=600)
        microgrid_device['ES_3'] = electricStorage(capacity=3600,Pmax_in=600)
        microgrid_device['ES_4'] = electricStorage(capacity=3600,Pmax_in=600)
        microgrid_device['ES_5'] = electricStorage(capacity=3600,Pmax_in=600)
        microgrid_device['ABSC_1'] = absorptionChiller()
        microgrid_device['Boiler_1'] = boiler()
        microgrid_device['CS_1'] = coldStorage()
        microgrid_device['AC_1'] = airConditioner()
        microgrid_device['GT_1'] = gasTurbine()
        microgrid_device['DR_Heat_Load'] = DRHeatLoad()
        microgrid_device['ut'] = utility()
        microgrid_device['inv'] = inverter()
        self.device = microgrid_device
        self.NumOfTime = 96
    def getKey(self,type):
        return [key for key in self.device.keys() if isinstance(self.device[key], type)]
    def SOCUpdate(self, plan, nowtime):
        N_es = self.getKey(electricStorage)
        for es in N_es:
            self.device[es].SOCnow = plan[es + '电池电量'].loc[nowtime] / self.device[es].capacity

