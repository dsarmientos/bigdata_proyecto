'''
Created on Nov 24, 2012

@author: daniel
'''
from django.shortcuts import render_to_response

def home(request):
    return render_to_response('index.html')
    
