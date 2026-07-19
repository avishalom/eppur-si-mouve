# author vish
# webpage eppur-si.appspot.com
# email avishalom@gmail.com

# patent pending on moveable partially hidden captcha application.
# use freely, but please attribute authorship where applicable.
# provided as is.
#
# by reading this line you will acknowledge that you have read this line.

import PIL
from PIL import Image, ImageDraw, ImageFont
import math
import numpy as np
from random import randint
from modules.default_conf import default_configurations
import os

fonts1 = ['BRADHITC.TTF', 'arial.ttf']       # in modules/
fonts2 = ['fonts/ariblk.ttf']               # Arial Black, in project root/fonts/
try:
    _mod = os.path.dirname(__file__)
    _root = os.path.dirname(_mod)
    fonts = ([os.path.join(_mod, ff) for ff in fonts1] +
             [os.path.join(_root, ff) for ff in fonts2])
except:
    fonts = [os.path.join(os.path.abspath('.'), ff) for ff in fonts1 + fonts2]


class CONF:
    '''
    The configuration class.
    Pre-programmed configurations live in default_conf; accessed as CONF.preconf.
    '''
    preconf = default_configurations

    def __init__(self, confn=0):
        for key, val in CONF.preconf[confn].items():
            setattr(self, key, val)

    def update(self, dict1):
        for key, val in dict1.items():
            if key in self.preconf[0]:
                setattr(self, key, int(val))


class VISCHA:
    '''
    Animated GIF generator.
    Create an instance with the required parameters (including the word to display),
    then call writeImage_fp(fp) to write the GIF to any file-like object.
    '''
    def __init__(self, word, confn=1, settings={}):
        '''
        settings: dict of CONF fields to override (passed as GET variables from the web layer).
        '''
        self.CONF = CONF(confn)
        self.CONF.update(settings)
        self.word = self._rand_image_word(word)

        self.background = self._this_many_words(self.CONF.wordCount, (self.CONF.width, self.CONF.height))
        self.foreground = self._get_net()
        self.bgSH = [0, -1, 0]
        self.wSH = [self.CONF.width//2 - self.word.size[0]//2,
                    self.CONF.height//2 - self.word.size[1], 0]
        self.foreSH = [self.CONF.dx, self.CONF.dy, 0]
        self.angle = 0

        if self.CONF.texture:
            self.word_noise = _make_noise(self.word.size)
            self.bg_noise   = _make_noise((self.CONF.width, self.CONF.height))
            self.fg_noise   = _make_noise((self.CONF.width, self.CONF.height))

    def _rand_image_word(self, rword=None):
        '''Creates an image containing a single word.'''
        font1 = ImageFont.FreeTypeFont(fonts[self.CONF.font], self.CONF.font_size + randint(0, 20))
        ang = 0.1
        if rword is None:
            ang = 1
            rword = get_random_letters_image(randint(3, 9))
        bbox = font1.getbbox(rword)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        im = PIL.Image.new('L', (w, h))
        dr = ImageDraw.Draw(im)
        dr.text((-bbox[0], -bbox[1]), rword, font=font1, fill='white')
        return im.rotate(ang * 3 * randint(-10, 10), expand=True)

    def _this_many_words(self, n, sizes):
        '''Creates an image scattered with n random decoy words.'''
        image = PIL.Image.new('L', sizes)
        for aye in range(n):
            im = self._rand_image_word()
            image.paste(im, (randint(-100, sizes[1]), randint(-40, sizes[1])), mask=im)
        return image

    def _get_net(self):
        '''Generates the foreground grating mask.'''
        r, c, shape, sizes = (self.CONF.screen_r,
                               self.CONF.screen_d,
                               self.CONF.shape,
                               (self.CONF.width, self.CONF.height))
        im = PIL.Image.new('L', sizes)
        dr = ImageDraw.Draw(im)
        t = int(sizes[0] / r * 1.2) + 1
        shapes = [{'shift': 1,  'wshrink': 0.86666, 'func': dr.ellipse},
                  {'shift': 0,  'wshrink': 1,        'func': dr.rectangle},
                  {'shift': 1,  'wshrink': .5,       'func': dr.rectangle},
                  ][shape]
        t = int(t / shapes['wshrink'])
        for aye in range(t):
            for jay in range(t):
                shapes['func']((aye*r*shapes['wshrink'],
                                jay*r - r//2*(aye%2)*shapes['shift'],
                                aye*r*shapes['wshrink'] + c,
                                jay*r + c - r//2*(aye%2)*shapes['shift']),
                               fill='white')
        return im

    def _nextImage(self, move=True):
        '''Generates the next frame.'''
        if move:
            imb = rollshift(self.background, self.bgSH)
            imw = self.word.rotate(self.wSH[2])
            imf = rollshift(self.foreground, self.foreSH, wobble=self.CONF.wobble)
            if self.CONF.texture:
                # Apply the same transforms to noise layers so they track their mask layers.
                # rollshift mutates in-place, so calling it with the same shift vector
                # advances both the mask and the noise by the same amount each frame.
                bg_tex = rollshift(self.bg_noise, self.bgSH)
                fg_tex = rollshift(self.fg_noise, self.foreSH)  # wobble=0 in texture preset
        else:
            imb = self.background
            imw = self.word
            imf = self.foreground
            if self.CONF.texture:
                bg_tex = self.bg_noise
                fg_tex = self.fg_noise

        im2 = Image.new('L', imb.size, self.CONF.bgColor)

        if self.CONF.texture:
            pastmask_texture(im2, imb, (0, 0), bg_tex)
            pastmask_texture(im2, imw, tuple(map(int, self.wSH[:2])), self.word_noise)
            pastmask_texture(im2, Image.eval(imf, lambda x: 255-x), (0, 0), fg_tex)
        else:
            pastmask(im2, imb, (0, 0), self.CONF.bgwColor)
            pastmask(im2, imw, map(int, self.wSH[:2]), self.CONF.fgColor)
            pastmask(im2, Image.eval(imf, lambda x: 255-x), (0, 0), self.CONF.screenColor)

        if move:
            self.wSH[0] += self.CONF.height/25 * math.cos(self.angle)
            self.wSH[1] += self.CONF.height/25 * math.sin(self.angle)
            self.angle += math.pi/18
            self.bgSH[1] = 1 if math.cos(self.angle) > 0 else -1
        return im2

    def writeImage_fp(self, Fp):
        '''
        Write the animated GIF to a file pointer.
        Caller is responsible for opening and closing the pointer.
        '''
        frames = [self._nextImage() for _ in range(36)]
        frames[0].save(
            Fp,
            format='GIF',
            save_all=True,
            append_images=frames[1:],
            duration=int(self.CONF.duration * 10),  # hundredths of sec → ms
            loop=0,
        )


# Utilities

def _make_noise(size):
    '''Returns a random white-noise PIL image of the given (width, height).'''
    arr = np.random.randint(0, 256, (size[1], size[0]), dtype=np.uint8)
    return PIL.Image.fromarray(arr, mode='L')

def pastmask(base, topmask, xy, colour):
    '''Paste a solid colour through a mask onto base.'''
    base.paste(Image.new('L', topmask.size, colour), tuple(xy), mask=topmask)

def pastmask_texture(base, mask, xy, texture):
    '''Paste a noise texture through a mask onto base.'''
    base.paste(texture, tuple(xy), mask=mask)

def rollshift(img, xyt, keep=False, wobble=0):
    '''Scroll and optionally rotate an image (mutates in place).'''
    szx, szy = img.size
    im2 = scroll(roll(img, xyt[0]), xyt[1]).rotate(xyt[2] + randint(-1, 1)*wobble, expand=True)
    s2x, s2y = im2.size
    box = (s2x-szx)//2, (s2y-szy)//2, (s2x+szx)//2, (s2y+szy)//2
    return im2.crop(box)

def roll(image, delta):
    '''Wrap an image horizontally by delta pixels.'''
    xsize, ysize = image.size
    delta = delta % xsize
    if delta == 0:
        return image
    part1 = image.crop((0, 0, delta, ysize))
    part2 = image.crop((delta, 0, xsize, ysize))
    image.paste(part2, (0, 0, xsize-delta, ysize))
    image.paste(part1, (xsize-delta, 0, xsize, ysize))
    return image

def scroll(image, delta):
    '''Wrap an image vertically by delta pixels.'''
    xsize, ysize = image.size
    delta = delta % ysize
    if delta == 0:
        return image
    part1 = image.crop((0, 0, xsize, delta))
    part2 = image.crop((0, delta, xsize, ysize))
    image.paste(part2, (0, 0, xsize, ysize-delta))
    image.paste(part1, (0, ysize-delta, xsize, ysize))
    return image

def get_random_letters_image(sz):
    return ' '.join(map(chr, [randint(48, 123) for _ in range(sz)]))


def main():
    for aye in range(4):
        v = VISCHA('Example 32', aye)
        with open('ffexample{}.gif'.format(aye), 'wb') as FP:
            v.writeImage_fp(FP)


if __name__ == '__main__':
    main()
    input()
