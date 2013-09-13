# author vish 
# webpage eppur-si.appspot.com
# email avishalom@gmail.com
# based entirely on images2gif in the visvis package .
#
# ##################     see notice for that package below this line 
#
#   Copyright (c) 2010, Almar Klein, Ant1, Marius van Voorden
#
#   This code is subject to the (new) BSD license:
#
#   Redistribution and use in source and binary forms, with or without
#   modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <organization> nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY 
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

##
##
##

import PIL
from images2gif import checkImages,GifWriter
## Exposed functions

def writeGifFp(FP, images, duration=0.1, repeat=True, dither=False, 
                nq=0, subRectangles=True, dispose=None):
    """ writeGif(filename, images, duration=0.1, repeat=True, dither=False,
                    nq=0, subRectangles=True, dispose=None)
    
    Write an animated gif from the specified images.
    
    Parameters
    ----------
    FP : the file pointer - 
    images : list
        Should be a list consisting of PIL images or numpy arrays.
        The latter should be between 0 and 255 for integer types, and
        between 0 and 1 for float types.
    duration : scalar or list of scalars
        The duration for all frames, or (if a list) for each frame.
    repeat : bool or integer
        The amount of loops. If True, loops infinitetely.
    dither : bool
        Whether to apply dithering
    nq : integer
        If nonzero, applies the NeuQuant quantization algorithm to create
        the color palette. This algorithm is superior, but slower than
        the standard PIL algorithm. The value of nq is the quality
        parameter. 1 represents the best quality. 10 is in general a
        good tradeoff between quality and speed. When using this option, 
        better results are usually obtained when subRectangles is False.
    subRectangles : False, True, or a list of 2-element tuples
        Whether to use sub-rectangles. If True, the minimal rectangle that
        is required to update each frame is automatically detected. This
        can give significant reductions in file size, particularly if only
        a part of the image changes. One can also give a list of x-y 
        coordinates if you want to do the cropping yourself. The default
        is True.
    dispose : int
        How to dispose each frame. 1 means that each frame is to be left
        in place. 2 means the background color should be restored after
        each frame. 3 means the decoder should restore the previous frame.
        If subRectangles==False, the default is 2, otherwise it is 1.
    
    """
    
    # Check PIL
    if PIL is None:
        raise RuntimeError("Need PIL to write animated gif files.")
    # Check images
    images = checkImages(images)
    
    # Instantiate writer object
    gifWriter = GifWriter()
    
    # Check loops
    if repeat is False:
        loops = 1
    elif repeat is True:
        loops = 0 # zero means infinite
    else:
        loops = int(repeat)
    
    # Check duration
    if hasattr(duration, '__len__'):
        if len(duration) == len(images):
            duration = [d for d in duration]
        else:
            raise ValueError("len(duration) doesn't match amount of images.")
    else:
        duration = [duration for im in images]
    
    # Check subrectangles
    if subRectangles:
        images, xy = gifWriter.handleSubRectangles(images, subRectangles)
        defaultDispose = 1 # Leave image in place
    else:
        # Normal mode
        xy = [(0,0) for im in images]
        defaultDispose = 2 # Restore to background color.
    
    # Check dispose
    if dispose is None:
        dispose = defaultDispose
    if hasattr(dispose, '__len__'):
        if len(dispose) != len(images):
            raise ValueError("len(xy) doesn't match amount of images.")
    else:
        dispose = [dispose for im in images]
    
    
    # Make images in a format that we can write easy
    images = gifWriter.convertImagesToPIL(images, dither, nq)
    
    # Write
    gifWriter.writeGifToFile(FP, images, duration, loops, xy, dispose)
    
