# author vish
# webpage eppur-si.appspot.com
# email avishalom@gmail.com

# patent pending on moveable partially hidden captcha application.
# use freely, but please attribute authorship where applicable.
# provided as is.
#
# by reading this line you will acknowledge that you have read this line.


import sys
from webob.multidict import UnicodeMultiDict
import cgi
import os
import datetime
import urllib
#from webapp2 import template
import webapp2
import jinja2
import os
import StringIO
from random import randint
import PIL
import numpy as np

from PIL import Image, ImageDraw 
sys.path.insert(0,os.path.dirname(__file__))
from modules import imagesH
import random
from google.appengine.ext import db
from google.appengine.api import users

class Record(db.Model):
    
    author = db.UserProperty()
    content = db.StringProperty(multiline=True)
    addr= db.StringProperty()
    user= db.StringProperty()
    verify= db.StringProperty()
    
    date = db.DateTimeProperty(auto_now_add=True)

def obf(key):
    num=int(key)
    obfs=str(173**num) 
# here is the plan .
# get_gif -> show the gif
# get_code -> store request, and give out the gifcode
# make_gif ->
class varpage(webapp2.RequestHandler):
    ''' debugging '''
    def get(self):
        self.response.out.write(repr(self.request.arguments()))
class MainPage(webapp2.RequestHandler):
    def get(self):
        #self.response.out.write(imagesH.fonts);return
        srp = self.request.path
        ## ## ## 
        dsr=dir(self.request)

        ## ## ## 
        if srp.startswith('/gif'): 
            #self.response.out.write ('getgf' + repr(srp) + " --- -- < <hr>" )
#            self.response.out.write(
            self.serve_request()
        elif srp.startswith('/robots'):
            self.serve_file('robots.txt')
        elif srp.startswith('/decode'):
            self.decode()
        elif srp.startswith('/get_code'):
            #self.response.out.write(self.request.remote_addr )
            id_= self.store_request()
            self.response.headers ['Content-Type'] = 'text/html'
            self.response.out.write(self.request.host_url+
                                    '/gif/'    + id_ +".gif" )
        elif srp.startswith('/direct_gif'):
            self.serve_straight()
            self.response.out.write(self.request.remote_user )
        else:
            self.serve_err('badcmd')
        return
        if srp.find('gif')>0 :
            return
            
        
        return
    def serve_file(self,fname):
            q = fname
          
            path = os.path.join (os.path.dirname (__file__), q)
        
            of = open(path)
            self.response.headers ['Content-Type'] = 'text/html'
            self.response.out.write (''.join(of.readlines()).replace('<!--$HOST_REPL-->',self.request.host_url))
    def serve_err(self,n):
        if n in ['','badcmd']:
            q = 'eppur.html'
          
            path = os.path.join (os.path.dirname (__file__), q)
        
            of = open(path)
            self.response.headers ['Content-Type'] = 'text/html'
            self.response.out.write (''.join(of.readlines()).replace('<!--$HOST_REPL-->',self.request.host_url))
        elif n in ['decode??']:
            self.response.headers ['Content-Type'] = 'text/html'
            self.response.out.write ('not a code')
        else:# n in ['nongif','nondigit','nonver']:
            self.serve({'word':n.replace('_',' '),'screen_d':15,'c':0,'wordCount':0})
            return
        #self.serve({'word':'what error'})
            #self.response.out.write('show main page')

    def store_request(self): # store the request string GET. 
        #self.response.out.write('store')
        handmade_key = db.Key.from_path('Record', 1)
        k=db.allocate_ids(handmade_key,1)[0]
        dg=dict(self.request.GET)
        if 'user' in dg or 'addr' in dg:
            return self.serve_default()            
        r=Record(content=str(dict(dg)),
                key=db.Key.from_path('Record',k)
                 )
        r.verify=''.join([chr(randint(65,89)) for dummy in range(4)])
        r.user=self.request.remote_user
        r.addr=self.request.remote_addr
        
        p=r.put()
        #self.response.write(repr(r.content)+ " "+" !@#!@# "+ repr(p.id()) + "<hr>")
        return r.verify+str(k)
    def serve_straight(self):
       # self.response.write('straight')
        self.serve(self.request.GET)
    def decode(self):
        n = self.request.path.split('/')[-1]
        if n[-4:] =='.gif': # ends with gif
            n2=n[4:-4]

        else:
            self.serve_err('decode??')# return non gif    
            return 
        if not n2.isdigit():
            self.serve_err('decode??')
            return
        r=Record.get_by_id(int(n2))
        
#        return(repr(r))
        if r and n[:4]==r.verify:
            self.response.headers ['Content-Type'] = 'text/html'
            self.response.out.write(self.request.host_url+'/direct_gif?'+
                                    '&'.join([a+'='+b for a,b in
                                          eval(r.content).items()])
                                    )
            return
        self.serve_err('decode??')
    def serve_request(self):
        n = self.request.path.split('/')[-1]
        if n[-4:] =='.gif': # ends with gif
            n2=n[4:-4]

        else:
            self.serve_err('not a gif')# return non gif    
            return 
        if not n2.isdigit():
            self.serve_err('bad code')
            return
        r=Record.get_by_id(int(n2))
        
#        return(repr(r))
        if r and n[:4]==r.verify:
            dd=eval(r.content)
            #            return repr(dd)+r.verify
            random.seed(r.verify)
            self.serve(dd)
            return 
        else:
            self.serve_err('WTF code')
        #self.response.write(';<br>%s -  "%s"'%(n[-3:],repr(dd)))
                                         
        return
    def rget(self,GGT,k,default):
        return GGT[k] if k in GGT else default
    
        

    def serve(self,dct):

#        try:
        word = self.rget(dct,'word','default')
        conf1 = int(self.rget(dct,'c','1'))
    #    if conf1>1:
     #       conf1=1
    
        v=imagesH.VISCHA(word,conf1,dct)

        self.response.headers['Content-Type']='image/gif'
        output = StringIO.StringIO()
        v.writeImage_fp(output)        #draw.rectangle((10, 10, 90, 90), fill="yellow", outline="red")
        self.response.out.write(output.getvalue())
        output.close() # VISH LAST EDIT
        return


app = webapp2.WSGIApplication([('/vars',varpage),('.*', MainPage),],
                              debug=True)
