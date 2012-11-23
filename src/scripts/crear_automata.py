import re
import pickle

import esm

import utils

de_re = re.compile('(^|\w+\s+)(de la|de los|del?)\s+(\w+)', re.I)
separator_re = re.compile(r'\s+')


def get_automata():
    gaceta = crear_gaceta()
    automata = esm.Index()
    agregar_nombres(automata, gaceta)
    automata.fix()
    with open('withh.pickle', 'w') as outf:
        pickle.dump(gaceta, outf)
    return automata


def crear_gaceta():
    with open('lista_congresistas_exp2.pickle', 'r') as infile:
        congresistas = pickle.load(infile)
    return congresistas


def expandir_nombres(congresista):
    primer_apellido, segundo_apellido = separar_nombres(
            congresista['apellidos'])
    primer_nombre, segundo_nombre = separar_nombres(
            congresista['nombres'])
    congresista['primer_nombre'] = primer_nombre
    congresista['segundo_nombre'] = segundo_nombre
    congresista['primer_apellido'] = primer_apellido
    congresista['segundo_apellido'] = segundo_apellido


def separar_nombres(nombres):
    def reemplazo(match):
        izq = match.group(1).strip()
        sep = match.group(2).strip().lower()
        if sep == 'de la':
            sep = 'de_la' 
        elif sep == 'de los':
            sep = 'de_los' 
        der = match.group(3).strip()
        txt = '%s %s_%s' % (izq, sep, der)
        return txt.strip()
    if de_re.search(nombres):
        nombres = de_re.sub(reemplazo, nombres)
    lista_nombres = separator_re.split(nombres)
    primer_nombre = ''
    segundo_nombre = ''
    palabras = len(lista_nombres)
    if palabras >= 1:
        primer_nombre = lista_nombres[0].replace('_', ' ')
    if palabras >= 2:
        segundo_nombre = lista_nombres[1].replace('_', ' ')
    return primer_nombre, segundo_nombre


def agregar_nombres(automata, gaceta):
    for congresista in gaceta:
        h1 = u'%s %s %s' % (congresista['primer_nombre'],
                            congresista['primer_apellido'],
                            congresista['segundo_apellido'])
        h2 = u'%s %s' % (congresista['nombres'],
                         congresista['apellidos'])
        h3 = u'%s %s %s' % (congresista['primer_nombre'],
                            congresista['segundo_nombre'],
                            congresista['primer_apellido'])
        heuristicas = set([h1, h2, h3])
        key = congresista['key']
        congresista['heuristicas'] = tuple(
            [utils.remove_accents(h) for h in heuristicas])
        [automata.enter(h, key) for h in congresista['heuristicas']]
