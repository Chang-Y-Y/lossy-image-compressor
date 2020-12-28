import struct
'''
Class for reading bmp file made by Chang Yun
This is a really simplified file reader for bmp
as it makes a bunch of assumptions and only
handles cases where it is a uncompressed
24 bit pixel bmp file. 

The reason I made it a class is in the hopes
that I can use this in the future again, and also
just make it easier to gain certain data
'''

class BMPReader:

    def __init__(self, bmp_file):
        
        # File data type section
        self.file_type = bmp_file.read(2).decode()
        self.file_size = struct.unpack("<I", bmp_file.read(4))[0]
        bmp_file.read(4)
        self.pixel_data_offset = struct.unpack("<I", bmp_file.read(4))[0]

        # Image Information data section

        self.header_size = struct.unpack("<I", bmp_file.read(4))[0]
        self.image_width = struct.unpack("<i", bmp_file.read(4))[0]
        self.image_height = struct.unpack("<i", bmp_file.read(4))[0]
        self.planes = struct.unpack("<H", bmp_file.read(2))[0]
        self.bits_per_pixel = struct.unpack("<H", bmp_file.read(2))[0]
        self.compression = struct.unpack("<I", bmp_file.read(4))[0]
        self.image_size = struct.unpack("<I", bmp_file.read(4))[0]
        self.Xpixels = struct.unpack("<i", bmp_file.read(4))[0]
        self.Ypixels = struct.unpack("<i", bmp_file.read(4))[0]
        self.total_colors = struct.unpack("<I", bmp_file.read(4))[0]
        self.important_colors = struct.unpack("<I", bmp_file.read(4))[0]

        self.image = []
        self.yuv_image = []

        padding = (self.image_width*3) % 4
        
        for y in range(self.image_height):
            self.image.append([])

        for y in range(self.image_height-1, -1, -1):
            for x in range(self.image_width):
                B = struct.unpack("B", bmp_file.read(1))[0]
                G = struct.unpack("B", bmp_file.read(1))[0]
                R = struct.unpack("B", bmp_file.read(1))[0]

                RGB = (R,G,B)

                self.image[y].append(RGB)
            if (padding != 0):
                bmp_file.read(4 - padding)

    def get_YUV_data(self):
        if len(self.yuv_image) != 0:
            return self.yuv_image
        yuv_lists = [[],[],[]]

        
        for y in range(self.image_height):
            yuv_lists[0].append([])
            yuv_lists[1].append([])
            yuv_lists[2].append([])
            for x in range(self.image_width):
                RGB = self.image[y][x]
                YUV = self.RGB_to_YUV(RGB)
                yuv_lists[0][y].append(YUV[0])
                yuv_lists[1][y].append(YUV[1])
                yuv_lists[2][y].append(YUV[2])
                

        return yuv_lists

    def RGB_to_YUV(self, rgb):

        
        Y = 0.2126*rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
        U = -0.09991 * rgb[0] + -0.33609 * rgb[1] + 0.436 * rgb[2]
        V = 0.615 * rgb[0] + -0.55861 * rgb[1] + -0.05639 * rgb[2]

        Y = round(Y)
        U = round(U)
        V = round(V)

        return (Y,U,V)
