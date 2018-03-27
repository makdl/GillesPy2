import sys
import statistics
from itertools import product
from timeit import default_timer as timer
from tqdm import tqdm
from basic_ssa_solver import BasicSSASolver
from basic_root_solver import BasicRootSolver
from optimized_ssa_solver import OptimizedSSASolver
from example_models import Trichloroethylene
from example_models import MichaelisMenten
from example_models import LacOperon
from example_models import Schlogl

modelList = [Trichloroethylene(), MichaelisMenten(), Schlogl()]
solverList = [BasicSSASolver, BasicRootSolver, OptimizedSSASolver]
timingList = []

# Get Ready for Jackson to 10x this.
for pair in product(modelList, solverList):
    model = pair[0]
    medianList = []
    for i in tqdm(range(100), desc=f'Model: {str(pair[0].name)}, Solver: {str(pair[1])}'):
        start = timer()
        model.run(solver=pair[1])
        stop = timer()
        medianList.append(stop - start)
    median = statistics.median(medianList)
    timingList.append([str(pair[0]), str(pair[1]), median])

for x in tqdm(range(len(solverList))):
    model = LacOperon()
    start = timer()
    model.run(solver=solverList[x])
    stop = timer()
    timingList.append([LacOperon, str(solverList[x]), stop - start])
