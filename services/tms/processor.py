# -*- coding: utf-8 -*-
"""
    services.tms.processor
    ~~~~~~~~~~~~~~~~~~~~~~

    The Processor takes care of manipulating the image-data for each zoom-level, like scaling and combining tiles. It's written
    as a wrapper class, in order to be able to use different image processors, however PIL is by far the fastest processor, compared
    to imagemagick. Maybe someone cares to write a cairo processor some day...

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import os
import StringIO
import math

try:
    import PythonMagick
except ImportError:
    pass
try:
    import PIL
    import Image,ImageDraw,ImageFont,ImageChops
except ImportError:
    pass


class Processor(object):
    """The processor wrapper class"""
    valid = True
    
    def __init__(self,config):
        processors = {'PythonMagick': _PythonMagickProcessor, 'PIL': _PILProcessor}
        if config.get('map','processor') in processors:
            try:
                __import__(config.get('map','processor'))
                self.processor = processors[config.get('map','processor')](config)
                self.offline_image = self.processor.offline_image
                self.notfound_image = self.processor.notfound_image
            except ImportError:
                self.valid = False
        else:
            self.valid = False


    def get_image(self,**kwargs):
        """Wrapper function to get the image"""
        return self.processor._get_image(**kwargs)
    def resize_image(self, *args):
        """Wrapper function to resize the image"""
        return self.processor._resize_image(*args)
    def compose_image(self, *args):
        """Wrapper function to compose the image"""
        self.processor._compose_image(*args)
    def write_tile(self,*args):
        """Wrapper function to write the tile to disk"""
        self.processor._write_tile(*args)
    def write_helpers(self,*args):
        """Wrapper function to write image helpers like the opaque 404.png"""
        self.processor._write_helpers(*args)
        
        
class _PythonMagickProcessor:
    """
    this only serves as an example how to use the processor wrapper class. PIL is the only maintained implementation currently.
    PythonMagick proved to be about 50% slower than PIL during tests.
    """
    
    def __init__(self,config):
        self.config = config
        self.notfound_image = PythonMagick.Image("256x256","#F0000000")
        self.offline_image = PythonMagick.Image("256x256", "#363636")
        self.offline_image.magick('RGBA')
        self.offline_image.font(os.path.join(self.config.location,'media/bitstream-vera/VeraBd.ttf'))
        self.offline_image.fillColor('#494949')
        self.offline_image.fontPointsize(30)
        self.offline_image.annotate("not available", PythonMagick._PythonMagick.GravityType.CenterGravity)
        
    def _get_image(self,file=None,data=None):
        """Open the image from the local path, used by the grabber"""
        if file:
            file = open('%s.%s' % (os.path.join(self.config.tilepath,str(file[0]),str(int(file[1])),str(int(file[2]))),self.config.get('map','format')),'r')
            blob = PythonMagick.Blob(file.read())
            return PythonMagick.Image(blob)
        elif data:
            try:
                blob = PythonMagick.Blob(data)
                image = PythonMagick.Image(blob)
                return image
            except RuntimeError:
                return self.offline_image
            return image
        else: 
            return PythonMagick.Image("256x256","#F0000000")
            
    def _resize_image(self, image, size_x, size_y):
        """Resizes the image to a certain size"""
        image.sample(PythonMagick._PythonMagick.Geometry(size_x, size_y))
        return image
        
    def _compose_image(self, canvas, image, pos_x, pos_y):
        """Compose a tile by combining it with another"""
        canvas.composite(image,pos_x,pos_y,PythonMagick._PythonMagick.CompositeOperator.OverCompositeOp)
        
    def _write_tile(self,image,tile):
        """Writes the actual tile configuration to disk"""
        try:
            os.makedirs(os.path.join(self.config.tilepath,str(tile[0]),str(tile[1])))
        except os.error:
            pass
        image.write(os.path.join(self.config.tilepath,str(tile[0]),str(tile[1]),str('%s.%s' % (tile[2],self.config.get('map','format')))))
        
    def _write_helpers(self):
        """Helpers like the 404 image"""
        self.notfound_image.write(os.path.join(self.config.tilepath,'404.png'))


class _PILProcessor:
    """The default image processor uses PIL. Quite ok results with it so far"""

    def __init__(self,config):
        self.config = config
        self.notfound_image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        self.offline_image = Image.new('RGBA', (256, 256), '#363636')
        self.ll_background = Image.new("RGBA", (256, 256), '#1d475f')
        self.draw = ImageDraw.Draw(self.offline_image)
        self.font = ImageFont.truetype(os.path.join(self.config.location,'media/bitstream-vera/VeraBd.ttf'), 30)
        self.draw.text((17,108), "not available",fill='#494949',font=self.font)
        
    def _get_image(self,file=None,data=None):
        """Open the image from the local path, used by the grabber"""
        if file:
            return Image.open(os.path.join(self.config.tilepath,str(file[0]),str(int(file[1])),str('%s.%s' % (int(file[2]),self.config.get('map','format')))))
        elif data:
            try:
                image = Image.open(StringIO.StringIO(data))
                return image
            except IOError:
                return self.offline_image
            return image
        else: 
            return Image.new("RGBA", (256, 256), (0, 0, 0, 0))
            
    def _resize_image(self, image, size_x, size_y):
        """Resizes the image to a certain size"""
        return image.resize((size_x,size_y))
        
    def _compose_image(self, canvas, image, pos_x, pos_y):
        """Compose a tile by combining it with another"""
        canvas.paste(image,(pos_x,pos_y))
        
    def _write_tile(self,image,z,cell):
        """Writes the actual tile configuration to disk"""
        try:
            path = os.path.join(self.config.tilepath,str(z),str(int(cell['z'][z]['x'])))
            print path
            os.makedirs(os.path.join(self.config.tilepath,str(z),str(int(cell['z'][z]['x']))))
        except os.error: pass
        target = os.path.join(self.config.tilepath,str(z),str(int(cell['z'][z]['x'])),str('%s.%s' % (int(cell['z'][z]['y']),self.config.get('map','format'))))
        try: 
            image.save(target,'PNG')
        except IOError: 
            self.offline_image.save(target,'PNG')
        if self.config.getboolean('service','ll_support') and z >= 11:
            regions_per_tile = math.pow(2,abs(z - self.config.getint('map','raw_ztop')))
            regions_from_top = int(regions_per_tile * (cell['z'][z]['x']%1))
            regions_from_left = int(regions_per_tile * (cell['z'][z]['y']%1))
            tile_name_x = int(cell['z'][self.config.getint('map','raw_ztop')]['x']) - regions_from_top
            tile_name_y = int(cell['z'][self.config.getint('map','raw_ztop')]['y']) - regions_from_left
            #print '%s,%s (%s:%s,%s)' % (tile_name_x,tile_name_y,z,regions_from_top,regions_from_left)
            target = '%s/ll/map-%s-%s-%s-objects.jpg' % (self.config.tilepath,str(abs((self.config.getint('map','raw_ztop')+1) - z)),str(tile_name_x),str(tile_name_y))
            if len(image.split()) == 4:
                image = image.transpose(Image.FLIP_TOP_BOTTOM)
                r,g,b,a = image.split()
                image = Image.composite(image,self.ll_background,a)
            try: image.save(target,'JPEG')
            except IOError: self.offline_image.save(target,'JPEG')
                
    def _write_helpers(self):
        """Helpers like the 404 image"""
        self.notfound_image.save(os.path.join(self.config.tilepath,'404.png'), 'PNG')    