from importFile import *
from microgrid_Model import *
import pandas as pd
import matplotlib.pyplot as plt
import optimizationModel,microgridStructure
def NBI_solver(mdl,objs,max_layer=3):
    import numpy as np
    import copy
    #得到多边形顶点
    CHULL = list()
    for obj in objs:
        mdl.objective = Objective(rule=lambda mdl:1000*obj(mdl)+sum(obj1(mdl) for obj1 in objs))
        xfrm = TransformationFactory('gdp.chull')
        xfrm.apply_to(optimalDispatch)
        solver = SolverFactory('gurobi')
        solver.solve(optimalDispatch)
        point = np.array([value(obj(optimalDispatch)) for obj in objs])
        CHULL.append({'point':point,
                      'result':optimizationModel.retriveResult(microgrid_data,case,optimalDispatch),
                      'objective':obj.__name__})
   #计算CHULL的法向量ns(求解NULL SPACE)
    ref = CHULL[0]['point']
    A = np.matrix([c['point'] - ref for c in CHULL[1:]])
    u, s, vh = np.linalg.svd(A)
    nnz = (s>0.01).sum()
    ns = np.array(vh[nnz:].tolist()[0])
    if ns[0]>=0:
        ns = -ns
    if (ns<0).sum() != len(ns):
        raise Exception
    def solve_within_region(polygon,mdl,now_layer):
        centoid = np.sum(polygon,axis=0)/len(polygon)
        ins = copy.deepcopy(mdl)
        ins.name = str(now_layer) + str(np.random.random())
        ins.t_len = Var()
        ins.objective = Objective(rule=lambda mdl:-mdl.t_len)
        ins.add_cons = Constraint(range(len(objs)),rule = lambda mdl,k:centoid[k] + mdl.t_len * ns[k] == objs[k](mdl))
        xfrm = TransformationFactory('gdp.bigM',bigM=1000000000)
        xfrm.apply_to(ins)
        solver = SolverFactory('gurobi')
        result = solver.solve(ins)
        if result.solver.termination_condition == TerminationCondition.optimal:
            res = [{'point': np.array([value(obj(ins)) for obj in objs]),
                    'result': optimizationModel.retriveResult(microgrid_data, case, ins),
                    'objective': ins.name}]
        else:
            res = []
        if now_layer >= max_layer:
            return res
        else:
            for p in polygon:
                res.extend(solve_within_region([c if not np.array_equal(c,p) else centoid for c in polygon],mdl,now_layer+1))
            return res
    # print('U = ',u)
    # print('S = ',s)
    # print('V = ',vh)
    #网格划分CHULL,分治算法
    CHULL.extend(solve_within_region([c['point'] for c in CHULL], mdl, now_layer=1))

    return CHULL
def Bilevel_NBI_solver(mdl,objs,max_layer=3):
    import numpy as np
    import copy
    #得到多边形顶点
    CHULL = list()
    for obj in objs:
        ins = copy.deepcopy(mdl)
        ins.name = str(np.random.random())
        mdl.sub.objective = Objective(rule=lambda mdl:1000*obj(mdl)+sum(obj1(mdl) for obj1 in objs))
        mdl.objective = Objective(rule=lambda mdl: - 1000*obj(mdl.sub) - sum(obj1(mdl.sub) for obj1 in objs))
        xfrm = TransformationFactory('bilevel.linear_mpec')
        xfrm.apply_to(ins)
        xfrm = TransformationFactory('mpec.simple_disjunction')
        xfrm.apply_to(ins)
        xfrm = TransformationFactory('gdp.bigM',bigM=1000000000)
        xfrm.apply_to(ins)
        solver = SolverFactory('gurobi')
        solver.solve(ins)
        point = np.array([value(obj(ins.sub)) for obj in objs])
        CHULL.append({'point':point,
                      'result':optimizationModel.retriveResult(microgrid_data,case,ins),
                      'objective':obj.__name__})
   #计算CHULL的法向量ns(求解NULL SPACE)
    ref = CHULL[0]['point']
    A = np.matrix([c['point'] - ref for c in CHULL[1:]])
    u, s, vh = np.linalg.svd(A)
    nnz = (s>0.01).sum()
    ns = np.array(vh[nnz:].tolist()[0])
    if ns[0]>=0:
        ns = -ns
    if (ns<0).sum() != len(ns):
        raise Exception
    def solve_within_region(polygon,mdl,now_layer):
        centoid = np.sum(polygon,axis=0)/len(polygon)
        ins = copy.deepcopy(mdl)
        ins.name = str(now_layer) + str(np.random.random())
        ins.sub.t_len = Var()
        ins.sub.objective = Objective(rule=lambda mdl:-mdl.t_len)
        ins.sub.add_cons = Constraint(range(len(objs)),rule = lambda mdl,k:centoid[k] + mdl.t_len * ns[k] == objs[k](mdl))
        xfrm = TransformationFactory('gdp.bigM',bigM=1000000000)
        xfrm.apply_to(ins)
        solver = SolverFactory('gurobi')
        result = solver.solve(ins)
        if result.solver.termination_condition == TerminationCondition.optimal:
            res = [{'point': np.array([value(obj(ins.sub)) for obj in objs]),
                    'objective': ins.name}]
        else:
            res = []
        if now_layer >= max_layer:
            return res
        else:
            for p in polygon:
                res.extend(solve_within_region([c if not np.array_equal(c,p) else centoid for c in polygon],mdl,now_layer+1))
            return res
    # print('U = ',u)
    # print('S = ',s)
    # print('V = ',vh)
    #网格划分CHULL,分治算法
    CHULL.extend(solve_within_region([c['point'] for c in CHULL], mdl, now_layer=1))

    return CHULL
'''Initialize a special case of microgrid'''
case = microgridStructure.case_PS
'''Load input data'''
microgrid_data = pd.read_excel('input_PS.xlsx')
'''Construct base model'''
optimalDispatch = optimizationModel.DayAheadModel(microgrid_data,case,range(96),mode='max')
'''Setting Goals'''
obj_min_cost = optimalDispatch.sub.obj_simple#最小化运行成本
def obj_min_CO2(mdl):
    return 0.5*mdl.Fuel_Cost(mdl)
'''Solve the model'''
CHULL = Bilevel_NBI_solver(optimalDispatch,[obj_min_cost,obj_min_CO2],max_layer=2)
for c in CHULL:
    print(c['objective'],' : ',c['point'])