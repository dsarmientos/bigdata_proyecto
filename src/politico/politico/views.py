'''
Created on Nov 24, 2012

@author: daniel
'''
import redis
from django.shortcuts import render_to_response
from django.utils import simplejson
import logging

logger = logging.getLogger('console')

r = redis.StrictRedis(host='localhost', port=6379, db=0)


def home(request):
    word_count = r.zrevrange('indice:global', 0, 249, True)
    max_f = max((wc[1] for wc in word_count))
    f = lambda f: (f / max_f)
    word_list = [{'text':wc[0], 'size':f(wc[1])} for wc in word_count]
    logger.info(word_list[:15])
    for w in word_list:
        assert w['size'] <= 1 and w['size'] > 0
    words = simplejson.dumps(word_list);
    return render_to_response('index.html', {'words':words})
    
