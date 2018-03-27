from .gillespy2 import *

import re
from functools import partial

def interior_trigonometric(token_list, model):
    trig_dict = {"sin": "numpy.sine",
                 "cos": "numpy.cos",
                 "tan": "numpy.tan"}
    return "{}{}".format(trig_dict[token_list[0]], parenthetical_expansion(token_list[1], model))


def interior_exponentiation(ts, model, species, out):
    pass
    # base = []
    # power = []
    # for index in range(1, len(ts)-1):
    #     if "," in ts[index]:
    #         base = ts[:index+1]
    #         power = ts[index+2:]
    #         break
    # if base:
    #     if len(base) == 1:
    #         base = str(base)
    #         if base in model.listOfSpecies.keys():
    #             base = "model.listOfSpecies['{}'].initial_value".format(base)
    #     else:
    #
    # try:
    #     if base in model.listOfSpecies.keys():
    #         base = "model.listOfSpecies['{}'].initial_value".format(base)
    #     if power in model.listOfSpecies.keys():
    #         power = "model.listOfSpecies['{}'].initial_value".format(power)
    #     out += "{}{}**{}{}".format(left_parentheses, base, power, right_parentheses)
    #     if not ts:
    #         return out
    #     else:
    #         return function_rules_parser(ts, model, species, output_string=out)
    # except Exception as e:
    #     print(e)


def interior_comparator(self, token):
    pass


def interior_conjunction(self, token):
    pass


def interior_piecewise(self, token):
    pass


def parenthetical_expansion(ts, model, species, out):
    interior_expression = []
    balanced_parentheses = 0
    for token in ts:
        if token == ")":
            if balanced_parentheses == 0:
                return function_rules_parser(interior_expression, model, species)
            else:
                interior_expression.append(ts.pop(0))
        else:
            continue


def tokenizer(input_rule):
    return [x for x in re.split(r'(\s|\(|\))', input_rule) if x != ' ' and len(x) != 0]


def function_rules_parser(token_stream, model, species, output_string=""):
    operand_list = ['+', '-', '*', '/']
    function_dict = {'sin': partial(interior_trigonometric),
                     'pow': partial(interior_exponentiation),
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
        # I'm assuming that the intention is that these are just values to set the inital population.
        # The spec document says that's not cool, but y'know...
        if len(token_stream) == 1 and output_string == "":
            model.listOfSpecies[species].initial_value = float(token_stream)
            return
    finally:
        token = token_stream.pop(0)
        if token == '(' or token == ')':
            output_string += token
            if not token_stream:
                return output_string
            else:
                return function_rules_parser(token_stream, model, species, output_string=output_string)
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
        else:
            try:
                float(token)
                output_string += token
                return function_rules_parser(token_stream, model, species, output_string=output_string)
            except (TypeError, ValueError):
                if token in model.listOfSpecies.keys():
                    output_string += "model.listOfSpecies['{}'].initial_value".format(token)
                    if not token_stream:
                        return output_string
                    return function_rules_parser(token_stream, model, species, output_string=output_string)
                else:
                    print("Could not parse string token: {}, please check model.".format(token))
