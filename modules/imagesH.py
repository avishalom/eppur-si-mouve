# author vish 
# webpage eppur-si.appspot.com
# email avishalom@gmail.com

# patent pending on moveable partially hidden captcha application.
# use freely, but please attribute authorship where applicable.
# provided as is.
#
# by reading this line you will acknowledge that you have read this line.

import PIL
from PIL import Image ,ImageDraw , ImageFont 
import math
import numpy as np
from random import randint
import images2gif_extension #import writeGifFp
from default_conf import default_configurations
import os

fonts1 = ['BRADHITC.TTF','arial.ttf']
# kept in a local directory. I had some issues with the case of the filenames in google appengine.
# didn't take mixed caps  all small or all capital ok.
try:
    fonts = [os.path.join(os.path.dirname(__file__) ,ff) for ff in fonts1]
except:
    fonts = [os.path.join(os.path.abspath('.') ,ff) for ff in fonts1]

class CONF:
    '''
the configuration class .
there a are some preprogrammed configurations in the file default_conf. 
 accessed as CONF.preconf

'''
    preconf = default_configurations
    
    def __init__(self,confn=0):
        
        for key,val in CONF.preconf[confn].items():
            setattr(self,key,val)
    def update(self,dict1):
        for key,val in dict1.items():#            if key not in['secure' ,'word']:
            if key in self.preconf[0]:
               setattr(self,key,int(val))


class VISCHA:
    '''
    this is the animated gif generator
    an instance is created with all the required parameters. including the "word" 
    it can then be written to a filepointer via the "writeImage" method. 
    a filepointer can be a static file or a stream. (e.g. dynamically generated web images)
    '''
    def __init__(self,word,confn=1,settings={}):
        '''
        settings takes in a dictionary with some of the fields in  CONF.preconf
        these are meant to be passed through GET variables.
        '''         
        self.CONF=CONF(confn)
        self.CONF.update(settings)
        self.word= self._rand_image_word(word)

        self.background = self._this_many_words(self.CONF.wordCount,(self.CONF.width,self.CONF.height)) # bg words
        
        self.foreground = self._get_net()
        self.bgSH=[0, -1, 0]
        self.wSH=[self.CONF.width/2-self.word.size[0]/2,
                  self.CONF.height/2-self.word.size[1],0]
        self.foreSH=[self.CONF.dx,self.CONF.dy,0]
        self.angle=0


    def _rand_image_word(self,rword=None):
        '''
        creates an image with a random word''' 
	#return fonts[self.CONF.font]
	
        font1 = ImageFont.FreeTypeFont(fonts[self.CONF.font],self.CONF.font_size+randint(0,20))
	#return None
        ang=0.1
        if rword==None:
            ang=1
            rword = get_random_letters_image(randint(3,9))
        size = font1.getsize(rword)
        im= PIL.Image.new('L',size)
        dr= ImageDraw.Draw(im)
#	return None
        dr.text((0,0),rword,font=font1,fill='white')
        return im.rotate(ang*3*randint(-10,10),expand=True)

    def _this_many_words(self,n,sizes):
        '''
            creates an image with several random words on it
        '''
        image = PIL.Image.new('L',sizes)
    
        for aye in range(n):
            im=self._rand_image_word()
            image.paste(im,(randint(-100,sizes[1]),
                            randint(-40,sizes[1])),
                            mask=im)
        return image

    def _get_net(self):
        '''
        this generates the foreground grating
        '''
        r,c,shape,sizes=(self.CONF.screen_r,
                         self.CONF.screen_d,
                         self.CONF.shape,
                        (self.CONF.width,self.CONF.height))
        im=PIL.Image.new('L',sizes)
        dr=ImageDraw.Draw(im)
        t=int(sizes[0]/r*1.2)+1
        shapes=[{'shift':1,
                 'wshrink':0.86666,
                 'func':dr.ellipse},
                {'shift':0,
                 'wshrink':1,
                 'func':dr.rectangle},
                {'shift':1,
                 'wshrink':.5,
                 'func':dr.rectangle},
                ][shape]
        t=int(t/shapes['wshrink'])
        for aye in range(t):
            for jay in range(t):
                shapes['func']((aye*r*shapes['wshrink'],
                            jay*r-r/2*(aye%2)*shapes['shift'],
                            aye*r*shapes['wshrink']+c,
                            jay*r+c-r/2*(aye%2)*shapes['shift']),fill='white')
        return im
    
    def _nextImage(self,move=True):
        '''
        generate the next in the series of images 
        '''
        if move :
            imb=rollshift(self.background,self.bgSH)
            imw=self.word.rotate(self.wSH[2])
            imf=rollshift(self.foreground,self.foreSH,wobble=self.CONF.wobble)
        else :
            imb = self.background
            imw = self.word
            imf = self.foreground
        im2=Image.new('L',imb.size,self.CONF.bgColor)
        pastmask(im2,imb,(0,0),self.CONF.bgwColor)
        pastmask(im2,imw,map(int,self.wSH[:2]),self.CONF.fgColor)
        pastmask(im2,Image.eval(imf,lambda x:255-x),
                 (0,0),self.CONF.screenColor)
        if move:
            self.wSH[0]+=self.CONF.height/25*math.cos(self.angle*1)
            self.wSH[1]+=self.CONF.height/25*math.sin(self.angle*1)
            self.angle+=math.pi/18
            self.bgSH[1]=1 if math.cos(self.angle) > 0 else -1
        return im2
	
    def writeImage_fp(self,Fp):
        '''
        write the animated gif to file pointer.
        it is callers responsibility to open and close the pointre
        '''
        images2gif_extension.writeGifFp(Fp,
                 [np.array(self._nextImage()) for dummy in range(36) ],duration=(self.CONF.duration/100.0))    



# some utilities 

def pastmask(base,topmask,xy,colour):
    '''
    paste one image on top of the other with a mask
        '''
    base.paste(Image.new('L',topmask.size,colour),tuple(xy),mask=topmask)
    
def rollshift(img,xyt,keep=False,wobble=0):
    '''
   scroll and rotate an image 
    '''
    szx,szy=img.size
    im2=scroll(roll(img,xyt[0]),xyt[1]).rotate(xyt[2]+randint(-1,1)*wobble,expand=True)
    s2x,s2y=im2.size
    box=(s2x-szx)/2,(s2y-szy)/2,(s2x+szx)/2,(s2y+szy)/2
    return im2.crop(box)
    

def roll(image, delta):
    "Rotate an image "

    xsize, ysize = image.size

    delta = delta % xsize
    if delta == 0: return image

    part1 = image.crop((0, 0, delta, ysize))
    part2 = image.crop((delta, 0, xsize, ysize))
    image.paste(part2, (0, 0, xsize-delta, ysize))
    image.paste(part1, (xsize-delta, 0, xsize, ysize))

    return image
def scroll(image, delta):
    "scroll an image up down , shifting it to one side, and wraping around"

    xsize, ysize = image.size

    delta = delta % ysize
    if delta == 0:
        return image

    part1 = image.crop((0, 0, xsize,delta,))
    part2 = image.crop((0, delta, xsize, ysize))
    image.paste(part2, (0, 0, xsize, ysize-delta))
    image.paste(part1, (0,ysize-delta, xsize, ysize))

    return image

def get_random_letters_image(sz):
    return ' '.join(map(chr,[randint(48,123)for dummy in range(sz)]))


def main():
    for aye in range(2):
        v=VISCHA('Example 32',aye)
        with open('ffexample{}.gif'.format(aye),'w') as FP:
            v.writeImage_fp(FP)           


if __name__ == '__main__':
    main()
    a = raw_input()
