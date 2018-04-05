import os
import gillespy2
import numpy
import re
from functools import partial
import math


def interior_trigonometric(ts, model, species, out):
    trig_dict = {"sin": "numpy.sine(",
                 "cos": "numpy.cos(",
                 "tan": "numpy.tan("}
    out += trig_dict[ts]
    return parenthetical_expansion(ts, model, species, out)


def interior_pow(ts, model, species, out):
    base = []
    power = []
    for index in range(1, len(ts) - 1):
        if "," in ts[index]:
            base = ts[:index + 1]
            power = ts[index + 2:]
            break
    if base:
        if len(base) == 1:
            base = str(base)
            if base in model.listOfSpecies.keys():
                base = "model.listOfSpecies['{}'].initial_value".format(base)
            else:
                try:
                    float(base)
                except (TypeError, ValueError) as e:
                    raise ParseError(
                        "Could not parse string token: {}, please check model. Exception: {}".format(base, e))
    try:
        if base in model.listOfSpecies.keys():
            base = "model.listOfSpecies['{}'].initial_value".format(base)
        if power in model.listOfSpecies.keys():
            power = "model.listOfSpecies['{}'].initial_value".format(power)
        out += "({}**{})".format(base, power)
        if not ts:
            return out
        else:
            return function_rules_parser(ts, model, species, output_string=out)
    except Exception as e:
        print(e)


def interior_exponentiation(ts, model, species, out):
    out += "math.exp("
    return parenthetical_expansion(ts, model, species, out)

def interior_comparator(self, token):
    pass


def interior_conjunction(self, token):
    pass


def interior_piecewise(self, token):
    pass


def parenthetical_expansion(ts, model, species, out):
    interior_expression = []
    balanced_parentheses = 1
    for token in ts:
        if token == ")":
            balanced_parentheses -= 1
            if balanced_parentheses == 0:
                return function_rules_parser(interior_expression, model, species)
            else:
                interior_expression.append(ts.pop(0))
        if token == "(":
            balanced_parentheses += 1
            continue
        else:
            continue


def tokenizer(input_rule):
    return [x for x in re.split(r'(\s|\(|\))', input_rule) if x != ' ' and len(x) != 0]


def function_rules_parser(token_stream, model, species, output_string=""):
    operand_list = ['+', '-', '*', '/']
    function_dict = {'sin': partial(interior_trigonometric),
                     'pow': partial(interior_pow),
                     'exp': partial(interior_exponentiation),
                     'gt': partial(interior_comparator),
                     'geq': partial(interior_comparator),
                     'lt': partial(interior_comparator),
                     'leq': partial(interior_comparator),
                     'eq': partial(interior_comparator),
                     'and': partial(interior_conjunction),
                     'piecewise': partial(interior_piecewise),
                    }
    try:
        # Observing some of the models, some of them just have integer values as there population rules.
        # I'm assuming that the intention is that these are just values to set the initial population.
        # The spec document says that's not cool, but y'know...
        if len(token_stream) == 1 and output_string == "":
            model.listOfSpecies[species].initial_value = float(token_stream)
            return
    finally:
        token = token_stream.pop(0)
        if token == '(':
            output_string += token
            if not token_stream:
                return output_string
            else:
                return parenthetical_expansion(token_stream, model, species, output_string)
        if token in operand_list:
            output_string += token
            if not token_stream:
                return output_string
            else:
                return function_rules_parser(token_stream, model, species, output_string=output_string)
        if token in function_dict.keys():
            try:
                return function_dict[token](token_stream, model, species, output_string)
            except Exception as e:
                print(e)
        if token in model.listOfSpecies.keys():
            output_string += "model.listOfSpecies['{}'].initial_value".format(token)
            if not token_stream:
                return output_string
            return function_rules_parser(token_stream, model, species, output_string=output_string)
        else:
            try:
                float(token)
                output_string += token
                return function_rules_parser(token_stream, model, species, output_string=output_string)
            except (TypeError, ValueError) as e:
                    raise ParseError("Could not parse string token: {}, please check model. Exception: {}".format(token, e))


def convert(filename, model_name=None, gillespy_model=None):
    try:
        import libsbml
    except ImportError:
        raise ImportError('libsbml is required to convert SBML files for GillesPy.')

    document = libsbml.readSBML(filename)

    errors = []

    errorCount = document.getNumErrors()
    if errorCount > 0:
        for i in range(errorCount):
            error = document.getError(i)
            converterCode = 0
            converterCode = -10

            errors.append(["SBML {0}, code {1}, line {2}: {3}".format(error.getSeverityAsString(), error.getErrorId(),
                                                                      error.getLine(), error.getMessage()),
                           converterCode])

    if min([code for error, code in errors] + [0]) < 0:
        return None, errors

    model = document.getModel()
    numOfTabs = 0

    if model_name == None:
        model_name = model.getName()

    if gillespy_model == None:
        gillespy_model = gillespy2.Model(name=model_name)

    gillespy_model.units = "concentration"

    for i in range(model.getNumSpecies()):
        species = model.getSpecies(i)

        if species.getId() == 'EmptySet':
            errors.append([
                              "EmptySet species detected in model on line {0}. EmptySet is not an explicit species in gillespy".format(
                                  species.getLine()), 0])
            continue

        name = species.getId()

        if species.isSetInitialAmount():
            value = species.getInitialAmount()
        elif species.isSetInitialConcentration():
            value = species.getInitialConcentration()
        else:
            rule = model.getRule(species.getId())

            if rule:
                msg = ""

                if rule.isAssignment():
                    msg = "assignment "
                elif rule.isRate():
                    msg = "rate "
                elif rule.isAlgebraic():
                    msg = "algebraic "

                msg += "rule"

                errors.append([
                                  "Species '{0}' does not have any initial conditions. Associated {1} '{2}' found, but {1}s are not supported in gillespy. Assuming initial condition 0".format(
                                      species.getId(), msg, rule.getId()), 0])
            else:
                errors.append([
                                  "Species '{0}' does not have any initial conditions or rules. Assuming initial condition 0".format(
                                      species.getId()), 0])

            value = 0

        if value < 0.0:
            errors.append([
                              "Species '{0}' has negative initial condition ({1}). gillespy does not support negative initial conditions. Assuming initial condition 0".format(
                                  species.getId(), value), -5])
            value = 0

        gillespySpecies = gillespy2.Species(name=name, initial_value=value)
        gillespy_model.add_species([gillespySpecies])

    for i in range(model.getNumParameters()):
        parameter = model.getParameter(i)
        name = parameter.getId()
        value = parameter.getValue()

        gillespyParameter = gillespy2.Parameter(name=name, expression=value)
        gillespy_model.add_parameter([gillespyParameter])

    for i in range(model.getNumCompartments()):
        compartment = model.getCompartment(i)
        name = compartment.getId()
        value = compartment.getSize()

        gillespyParameter = gillespy2.Parameter(name=name, expression=value)
        gillespy_model.add_parameter([gillespyParameter])

    # local parameters
    for i in range(model.getNumReactions()):
        reaction = model.getReaction(i)
        kineticLaw = reaction.getKineticLaw()

        for j in range(kineticLaw.getNumParameters()):
            parameter = kineticLaw.getParameter(j)
            name = parameter.getId()
            value = parameter.getValue()
            gillespyParameter = gillespy2.Parameter(name=name, expression=value)
            gillespy_model.add_parameter([gillespyParameter])

    # reactions
    for i in range(model.getNumReactions()):
        reaction = model.getReaction(i)
        name = reaction.getId()

        reactants = {}
        products = {}

        for j in range(reaction.getNumReactants()):
            species = reaction.getReactant(j)

            if species.getSpecies() == "EmptySet":
                errors.append([
                                  "EmptySet species detected as reactant in reaction '{0}' on line {1}. EmptySet is not an explicit species in gillespy".format(
                                      reaction.getId(), species.getLine()), 0])
            else:
                reactants[species.getSpecies()] = species.getStoichiometry()

        # get products
        for j in range(reaction.getNumProducts()):
            species = reaction.getProduct(j)

            if species.getSpecies() == "EmptySet":
                errors.append([
                                  "EmptySet species detected as product in reaction '{0}' on line {1}. EmptySet is not an explicit species in gillespy".format(
                                      reaction.getId(), species.getLine()), 0])
            else:
                products[species.getSpecies()] = species.getStoichiometry()

        # propensity
        kineticLaw = reaction.getKineticLaw()
        propensity = kineticLaw.getFormula()

        gillespyReaction = gillespy2.Reaction(name=name, reactants=reactants, products=products,
                                             propensity_function=propensity)

        gillespy_model.add_reaction([gillespyReaction])

    for i in range(model.getNumRules()):
        rule = model.getRule(i)

        t = []

        if rule.isCompartmentVolume():
            t.append('compartment')
        if rule.isParameter():
            t.append('parameter')
        elif rule.isAssignment():
            t.append('assignment')
        elif rule.isRate():
            t.append('rate')
        elif rule.isAlgebraic():
            t.append('algebraic')

        if len(t) > 0:
            t[0] = t[0].capitalize()

            msg = ", ".join(t)
            msg += " rule"
        else:
            msg = "Rule"

        errors.append(["{0} '{1}' found on line '{2}' with equation '{3}'. gillespy does not support SBML Rules".format(
            msg, rule.getId(), rule.getLine(), libsbml.formulaToString(rule.getMath())), -5])

    for i in range(model.getNumCompartments()):
        compartment = model.getCompartment(i)

        errors.append([
                          "Compartment '{0}' found on line '{1}' with volume '{2}' and dimension '{3}'. gillespy assumes a single well-mixed, reaction volume".format(
                              compartment.getId(), compartment.getLine(), compartment.getVolume(),
                              compartment.getSpatialDimensions()), -5])

    for i in range(model.getNumConstraints()):
        constraint = model.getConstraint(i)

        errors.append([
                          "Constraint '{0}' found on line '{1}' with equation '{2}'. gillespy does not support SBML Constraints".format(
                              constraint.getId(), constraint.getLine(), libsbml.formulaToString(constraint.getMath())),
                          -5])

    for i in range(model.getNumEvents()):
        event = model.getEvent(i)

        errors.append([
                          "Event '{0}' found on line '{1}' with trigger equation '{2}'. gillespy does not support SBML Events".format(
                              event.getId(), event.getLine(), libsbml.formulaToString(event.getTrigger().getMath())),
                          -5])

    for i in range(model.getNumFunctionDefinitions()):
        function = model.getFunctionDefinition(i)

        errors.append([
                          "Function '{0}' found on line '{1}' with equation '{2}'. gillespy does not support SBML Function Definitions".format(
                              function.getId(), function.getLine(), libsbml.formulaToString(function.getMath())), -5])

    return gillespy_model, errors


# if __name__ == '__main__':
#     import sys
#     import urllib2
#     import tempfile
#
#     sbml_list = ['http://www.ebi.ac.uk/biomodels-main/download?mid=BIOMD0000000054']
#
#     for sbml_file in sbml_list:
#         print("Testing 'convert()' for {0}".format(sbml_file))
#         if sbml_file.startswith('http'):
#             response = urllib2.urlopen(sbml_file)
#             tmp = tempfile.NamedTemporaryFile(delete=False)
#             tmp.write(response.read())
#             tmp.close()
#             ######
#             model, errors = convert(tmp.name)
#             print(os.linesep.join([error for error, code in errors]))
#             print("-----")
#             os.remove(tmp.name)
#             ######
#         else:
#             if not os.path.exists(sbml_file):
#                 raise Exception("Can not find file on disk '{0}'".format(sbml_file))
#             ######
#             model, errors = convert(sbml_file)
#             print(os.linesep.join([error for error, code in errors]))
#             ######

class ParseError(Exception):
    pass