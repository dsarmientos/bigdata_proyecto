import pickle

import esm


def get_automata():
    gaceta = cargar_gaceta()
    automata = esm.Index()
    agregar_nombres(automata, gaceta)
    automata.fix()
    return automata


def cargar_gaceta():
    with open('gaceta.pickle', 'r') as infile:
        congresistas = pickle.load(infile)
    return congresistas


def agregar_nombres(automata, gaceta):
    for persona in gaceta:
        [automata.enter(h, persona['key']) for h in persona['heuristicas']]
