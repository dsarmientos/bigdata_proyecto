import re
import pickle

import ahocorasick

import utils

de_re = re.compile('(^|\w+\s+)(de la|de los|del?)\s+(\w+)', re.I)
separator_re = re.compile(r'\s+')


def get_automata():
    gaceta = crear_gaceta()
    automata = ahocorasick.KeywordTree()
    agregar_nombres(automata, gaceta)
    automata.make()
    return automata


def crear_gaceta():
    with open('lista_congresistas_exp.pickle', 'r') as infile:
        congresistas = pickle.load(infile)
    return congresistas


def agregar_nombres(automata, gaceta):
    for congresista in gaceta:
        automata.add(
           utils.remove_accents(u'%s %s %s' % (congresista['primer_nombre'],
                          congresista['primer_apellido'],
                          congresista['segundo_apellido']))
         )
        automata.add(
           utils.remove_accents(u'%s %s' % (congresista['nombres'],
                       congresista['apellidos']))
         )
        automata.add(
           utils.remove_accents(u'%s %s %s' % (congresista['primer_nombre'],
                          congresista['segundo_nombre'],
                          congresista['primer_apellido']))
         )
