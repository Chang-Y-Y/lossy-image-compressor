from tkinter import Label, Button, Canvas, Tk, filedialog, PhotoImage, Frame
from BMPProcessor import BMPReader
from compressor import Compressor
import numpy
from PIL import Image, ImageTk
import struct
import math

class BMP_GUI:

    # Creating widgets for the gui
    def __init__(self, root):
        self.root = root
        self.root.title("Title")
        
        self.file_path = ""

        self.file_button = Button(self.root, text="Choose file", command=self.get_filepath)
        self.file_button.grid(row=0, column=0, sticky='w')

        self.file_label = Label(root, text="File Path: No file path selected")
        self.file_label.grid(row = 1, column=0, sticky='w')

        self.process_button = Button(root, text="Process file", state="disabled", command=self.process_file)
        self.process_button.grid(row=2, column=0, sticky='w')

        self.compression_ratio = Label(root, text="Compression Ratio: ")
        self.compression_ratio.grid(row=2, column=1, sticky='w')

        self.frame = Frame(root)
        self.frame.grid(row=3, column=0, sticky='w', columnspan=2)
        
        self.canvas1 = Canvas(self.frame,width=300, height=300, bg="white")
        self.canvas2 = Canvas(self.frame,width=300, height=300, bg="white")
        self.canvas1.pack(side="left")
        self.canvas2.pack(side="left")

        self.image_width = 0
        self.image_height = 0

        self.images = []
    
    # Simple function for the user to select the file
    def get_filepath(self):
        self.file_path = filedialog.askopenfilename(initialdir="Proj1_Q3_Sample_Inputs",filetypes=(("bmp","*.bmp"),("img", "*.IMG"),))
        if (self.file_path != ""):
            self.file_label["text"] = self.file_label["text"][0:11] + self.file_path
            self.process_button["state"] = "normal"
    
    # This is where all the file is read and processed
    # Ironically, this class doesn't do the actual reading
    # The actual reading happens in the other file
    def process_file(self):
        self.images = []
        compress = []
        compressor = Compressor()
        # If an img file, then read file, decode, decompress, and display
        # Else compress and encode, as well as decompress and display to compare
        if (self.file_path[-3:].lower() == "img"):
            binary_seq, encode_dict = self.read_img_file(self.file_path)
            y_new, u_new, v_new = compressor.decode_Huffman(binary_seq, encode_dict, self.image_height, self.image_width)
            for i in range(self.image_height):
                compress.append([])
                for j in range(self.image_width):
                    compress[i].append(self.YUV_to_RGB(y_new[i][j], u_new[i][j], v_new[i][j]))
            self.images.append(compress)
            self.images.append(compress)
            self.plot_image()
            return

        # use a BMPReader class to raed the file for us
        # code for this is in other file
        bmpreader = BMPReader(open(self.file_path, "rb"))

        # setting image height and width
        self.image_height = bmpreader.image_height
        self.image_width = bmpreader.image_width

        # Getting all the images and putting 
        # it into one list
        self.images.append(bmpreader.image)
        yuv = bmpreader.get_YUV_data()

        y_dct = compressor.DCT_transform(yuv[0], 0)
        u_dct = compressor.DCT_transform(yuv[1], 1)
        v_dct = compressor.DCT_transform(yuv[2], 1)

        dct_bits, encode_dict = compressor.Huffman_compress([y_dct, u_dct, v_dct])
        
        y_new = compressor.DCT_inverse_transform(y_dct, self.image_width, self.image_height, 0)
        u_new = compressor.DCT_inverse_transform(u_dct, self.image_width, self.image_height, 1)
        v_new = compressor.DCT_inverse_transform(v_dct, self.image_width, self.image_height, 1)
        
        for i in range(self.image_height):
            compress.append([])
            for j in range(self.image_width):
                compress[i].append(self.YUV_to_RGB(y_new[i][j], u_new[i][j], v_new[i][j]))
        self.images.append(compress)
        
        self.plot_image()
        compressed_size = self.write_to_file(self.get_file_name()+".img", encode_dict, dct_bits)
        self.compression_ratio.configure(text = "Compression Ratio: " + str(bmpreader.file_size/compressed_size))

    # Moving across the list and plotting the values onto the screen
    # Using pillow becuase any other methods I found were too slow
    # I was going to try another way but I had no time
    def plot_image(self):
        pil_image1 = Image.new('RGB', (self.image_width, self.image_height))
        pil_image2 = Image.new('RGB', (self.image_width, self.image_height))
        pixel_map1 = pil_image1.load()
        pixel_map2 = pil_image2.load()
        image1 = self.images[0]
        image2 = self.images[1]
        self.canvas1.configure(width=self.image_width, height=self.image_height)
        self.canvas2.configure(width=self.image_width, height=self.image_height)

        for y in range(self.image_height):
            for x in range(self.image_width):
                pixel_map1[x,y] = tuple(image1[y][x])
                pixel_map2[x,y] = tuple(image2[y][x])

        self.img = ImageTk.PhotoImage(pil_image1)
        self.img2 = ImageTk.PhotoImage(pil_image2)
        self.canvas1.create_image(0,0,anchor="nw", image=self.img)
        self.canvas2.create_image(0,0,anchor="nw", image=self.img2)

        if (image1 == image2):
            self.canvas2.pack_forget()
        else:
            self.canvas2.pack(side="left")

    def YUV_to_RGB(self, Y, U, V):
        R = round(Y + 1.28033 * V)
        G = round(Y -0.21482 * U -0.38509 * V )
        B = round(Y + 2.12798 * U)

        RGB = [R, G, B]

        for i in range(3):
            if RGB[i] > 255:
                RGB[i] = 255
            elif RGB[i] < 0:
                RGB[i] = 0

        return tuple(RGB)

    def get_file_name(self):
        index = len(self.file_path)-1

        while (self.file_path[index] != '/' and index != 0):
            index -= 1
        
        return (self.file_path[index+1:len(self.file_path)-4])

    def write_to_file(self, filename, encode_dict, sequence):

        file_size = 16
        with open(filename, "wb") as file:
            file.write(struct.pack(">I", self.image_width))
            file.write(struct.pack(">I", self.image_height))

            file.write(struct.pack(">I", len(encode_dict)))
            file.write(struct.pack(">I", int(len(sequence)/8)))

            for key, encode in encode_dict.items():
                file.write(struct.pack(">B", len(encode)))

                file.write(struct.pack(">I", int(encode, 2)))
                file.write(struct.pack(">h", key))
                file_size += 7

            for i in range(0, len(sequence), 8):
                file.write(struct.pack(">B", int(sequence[i:i+8],2)))
                file_size += 1
        return file_size
        
    def read_img_file(self, filename):

        encode_dict = {}
        encode_dict_size = 0
        binary_seq_size = 0
        binary_seq = ""
        
        with open(filename, "rb") as file:
            self.image_width = struct.unpack(">I", file.read(4))[0]
            self.image_height = struct.unpack(">I", file.read(4))[0]

            encode_dict_size = struct.unpack(">I", file.read(4))[0]
            binary_seq_size = struct.unpack(">I", file.read(4))[0]
            
            for i in range(encode_dict_size):
                encode_size = struct.unpack(">B", file.read(1))[0]
                encoding = struct.unpack(">I", file.read(4))[0]

                encoding = '{0:032b}'.format(encoding)
                encoding = encoding[len(encoding)-encode_size:]
                
                key = struct.unpack(">h", file.read(2))[0]
                encode_dict[encoding] = key
                
            for i in range(binary_seq_size):
                binary_seq = binary_seq + '{0:08b}'.format(struct.unpack(">B", file.read(1))[0])

        
        return binary_seq, encode_dict

    # Main function to calculate PSNR. Not used in the main compression phase
    def calculate_PSNR(self):
        MSE = 0
        
        for i in range(self.image_height):
            for j in range(self.image_width):
                for k in range(3):
                    MSE += (self.images[0][i][j][k] - self.images[1][i][j][k])**2
        MSE = MSE / (self.image_height * self.image_width * 3)

        MAX = 2**24 - 1
        PSNR = 20 * math.log(MAX, 10) - 10 * math.log(MSE, 10)
        print(PSNR)

root = Tk()
bmp_gui = BMP_GUI(root)
root.mainloop()

