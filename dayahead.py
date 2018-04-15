from importFile import *
from pyomo.bilevel import *
from microgrid_Model import *
import pandas as pd
import matplotlib.pyplot as plt
import microgridStructure
import numpy as np
from optimizationModel import *

'''Initialize a special case of microgrid'''
case = microgridStructure.case_IES
'''Load input data'''
microgrid_data = pd.read_excel('IES_SIMPLE.xlsx')

'''Construct base model'''
OD = DayAheadModel(microgrid_data,case,range(5))
Tmpc = 2
Lmpc = 4
# get the KKT conditions
subobj = 0
fix_all_var(OD)
for i in range(Tmpc):
    AddDayInSubModel(OD, i, microgrid_data, case)
    temp = getattr(OD.sub, 'MPC_' + str(i))
    xfrm = TransformationFactory('bilevel.linear_mpec')
    if i >= 1:
        prev = getattr(OD.sub, 'MPC_' + str(i-1))
        fix_all_var(prev)
        xfrm.apply_to(OD.sub,options={'submodel':'MPC_' + str(i)})
        unfix_all_vars(prev)
    else:
        xfrm.apply_to(OD.sub,options={'submodel':'MPC_' + str(i)})
    if i == Tmpc - 1:
        subobj += temp.obj_Cost(temp, range(Lmpc))
    else:
        subobj += temp.obj_Cost(temp, 0)
# set sub-problem objective///fix master vars///transform the sub-problem
OD.sub.o = Objective(expr=subobj,sense=maximize)
transform_sub(OD.sub)
unfix_all_vars(OD)
transform_master(OD)
#'''THIS IS A TEST'''
# #Transformation
# transform_master(OD)
# '''the base model is constructed'''
# OD.sub.deactivate()
# solver = SolverFactory('gurobi')
# res = solver.solve(OD)
# '''The KKT&G Algorithm begins'''
# OD.sub.activate()
# fix_all_var(OD)
# solver = SolverFactory('gurobi')
# res = solver.solve(OD.sub, tee=True,  # stream the solver output
#                    keepfiles=True,  # print the MILP file for examination
#                    symbolic_solver_labels=True)  # fix变量之后，submodel可以直接求解
lb = - np.inf
ub = np.inf
NumIter = 1
while 1:
    # solve the master problem
    print('Iteration num {0}'.format(NumIter))
    solver = SolverFactory('gurobi')
    OD.sub.deactivate()
    if NumIter >= 2:
        del OD.objective
        OD.objective = Objective(rule=lambda mdl: mdl.obj_Economical(mdl) + mdl.eta)
    res = solver.solve(OD)
    if res.solver.termination_condition == TerminationCondition.optimal:
        lb = value(OD.objective)
    elif res.solver.termination_condition == TerminationCondition.unbounded:
        lb = - np.inf
    if NumIter == 1:
        print('master problem optimal value is {0}'.format(lb))
        print('master problem optimal eta is None')
        print('the lower bound is updated to {0}'.format(-np.inf))
    else:
        print('master problem optimal value is {0}'.format(lb - value(OD.eta)))
        print('master problem optimal eta is {0}'.format(value(OD.eta)))
        print('the lower bound is updated to {0}'.format(lb))
    # solve the sub problem
    OD.sub.activate()
    fix_all_var(OD) #注意查看文档，fix变量的方法,fix master variables
    solver = SolverFactory('gurobi')
    # res = solver.solve(OD.sub,tee=True, #stream the solver output
    #                     keepfiles=True, #print the MILP file for examination
    #                     symbolic_solver_labels=True) #fix变量之后，submodel可以直接求解
    res = solver.solve(OD.sub)
    if res.solver.termination_condition == TerminationCondition.optimal:
        ub = min(ub,value(OD.obj_Economical(OD)) + value(OD.sub.o))
    elif res.solver.termination_condition == TerminationCondition.unbounded:
        ub = ub
    # add kkt cuts to master problem
    print('the sub-obj is {0}'.format(value(OD.sub.o)))
    print('the upper bound is updated to {0}'.format(ub))
    print([value(OD.sub.o)])
    add_kkt_cuts(OD, NumIter)
    unfix_all_vars(OD)
    NumIter += 1
