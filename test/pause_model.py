import sys
sys.path.append('./')
import gillespy2
import numpy as np
from gillespy2 import NumPySSASolver
from gillespy2 import TauLeapingSolver
from gillespy2 import ODESolver
import sys
np.set_printoptions(suppress=True)

class Oregonator(gillespy2.Model):

    def __init__(self, parameter_values=None):
        # Superclass initialization
        gillespy2.Model.__init__(self, name="Oregonator")

        # Species
        F = gillespy2.Species(name="F", initial_value=2)
        A = gillespy2.Species(name="A", initial_value=250)
        B = gillespy2.Species(name="B", initial_value=500)
        C = gillespy2.Species(name="C", initial_value=1000)
        P = gillespy2.Species(name="P", initial_value=0)
        self.add_species([F, A, B, C, P])

        # Parameters (rates)
        k1 = gillespy2.Parameter(name="k1", expression=2.0)
        k2 = gillespy2.Parameter(name="k2", expression=0.1)
        k3 = gillespy2.Parameter(name="k3", expression=104)
        k4 = gillespy2.Parameter(name="k4", expression=4e-7)
        k5 = gillespy2.Parameter(name="k5", expression=26.0)
        self.add_parameter([k1, k2, k3, k4, k5])

        # Reactions
        reaction1 = gillespy2.Reaction(name="reaction1",
                                       reactants={B: 1, F: 1},
                                       products={A: 1, F: 1},
                                       rate=k1)
        reaction2 = gillespy2.Reaction(name="reaction2",
                                       reactants={A: 1, B: 1},
                                       products={P: 1},
                                       rate=k2)
        reaction3 = gillespy2.Reaction(name="reaction3",
                                       reactants={A: 1, F: 1},
                                       products={A: 2, C: 1, F: 1},
                                       rate=k3)
        reaction4 = gillespy2.Reaction(name="reaction4",
                                       reactants={A: 2},
                                       products={P: 1},
                                       rate=k4)
        reaction5 = gillespy2.Reaction(name="reaction5",
                                       reactants={C: 1, F: 1},
                                       products={B: 1, F: 1},
                                       rate=k5)
        self.add_reaction([reaction1, reaction2, reaction3, reaction4, reaction5])

        self.timespan(np.linspace(0, 5, 501))


model = Oregonator()
if sys.argv[1] == 'NumPySSASolver':
    results = model.run(solver=NumPySSASolver)
elif sys.argv[1] == 'TauLeapingSolver':
    results = model.run(solver=TauLeapingSolver)
else:
    results = model.run(solver=ODESolver, t=500001)

print(results.to_array()[0][-1][0])
