import math
import numpy as np
import struct

class Compressor:

    def __init__(self):

        self.T = 0
        self.Q = 0
        self.zigzag_coordinates = []
        self.quantization_tables = []
        self.calculate_transform_matrix(8)
        self.calculate_zigzag_coordinates(8)
        self.calculate_quantization_matrix()
        self.tree = []
        self.encode_dict = {}

    def DCT_transform(self, matrix, quantization_type):
        n_rows = len(matrix)
        n_cols = len(matrix[0])
        numpy_matrix = np.array(matrix)
        dct = []

        for i in range(0, n_rows, 8):
            for j in range(0, n_cols, 8):
                temp = np.dot(np.dot(self.T, numpy_matrix[i:i+8, j:j+8]), self.T.transpose())
                temp = temp / self.quantization_tables[quantization_type]
                for cord in self.zigzag_coordinates:
                    dct.append(temp[cord[0], cord[1]])

        dct = np.array(dct)
        dct = np.round(dct, 0).astype(np.int16).tolist()
        return dct

    def DCT_inverse_transform(self, dct, width, height, quantization_type):
        new_matrix = [[0 for i in range(width)] for i in range(height)]

        grid = np.zeros(8*8).reshape(8,8)
        dct_index = 0

        for i in range(0, height, 8):
            for j in range(0, width, 8):
                for cord in self.zigzag_coordinates:
                    grid[cord[0]][cord[1]] = dct[dct_index]
                    dct_index += 1
                grid = grid * self.quantization_tables[quantization_type]
                grid = np.dot(np.dot(self.T.transpose(), grid), self.T)
                for y in range(8):
                    for x in range(8):
                        new_matrix[y+i][x+j] = grid[y,x]

        new_matrix = np.round(np.array(new_matrix),0).astype(np.int16).tolist()
        
        return new_matrix

    

    def calculate_transform_matrix(self, n):
        self.T = np.zeros((n,n))
        for i in range(n):
            if (i == 0):
                a = math.sqrt(1/n)
            else:
                a = math.sqrt(2/n)

            for j in range(n):
                temp = ((2*j + 1)*i*math.pi)/(2*n)
                self.T[i, j] = a * math.cos(temp)


    def calculate_zigzag_coordinates(self, n):

        order = [[] for i in range(n+n-1)]

        for i in range(n):
            for j in range(n):
                total = i + j

                if (total % 2 == 0):
                    order[total].insert(0, (i,j))
                else:
                    order[total].append((i,j))

        for i in order:
            for j in i:
                self.zigzag_coordinates.append(j)

    def calculate_quantization_matrix(self):
        luminance_quantization_table = np.array([[16,11,10,16,24,40,51,61],
                                                 [12,12,14,19,26,58,60,55],
                                                 [14,13,16,24,40,57,69,56],
                                                 [14,17,22,29,51,87,80,62],
                                                 [18,22,37,56,68,109,103,77],
                                                 [24,35,55,64,81,104,113,92],
                                                 [49,64,78,87,103,121,120,101],
                                                 [72,92,95,98,112,100,103,99]])
        chrom_quantization_table = np.array([[17,18,24,47,99,99,99,99],
                                            [18,21,26,66,99,99,99,99],
                                            [24,26,56,99,99,99,99,99],
                                            [47,66,99,99,99,99,99,99],
                                            [99,99,99,99,99,99,99,99],
                                            [99,99,99,99,99,99,99,99],
                                            [99,99,99,99,99,99,99,99],
                                           [99,99,99,99,99,99,99,99]])
        q = 40
        s = round(5000/q)
        
        for i in range(8):
            for j in range(8):
                luminance_quantization_table[i, j] = math.floor((s*luminance_quantization_table[i, j] + 50)/100)
                chrom_quantization_table[i, j] = math.floor((s*chrom_quantization_table[i, j] + 50)/100)
        
        self.quantization_tables.append(luminance_quantization_table)
        self.quantization_tables.append(chrom_quantization_table)

    def binary_insert(self, arr, low, high, val):
        if low == high:
            if arr[low][1] > val:
                return low
            return low + 1

        if low > high:
            return low

        mid = (low + high) // 2
        if (arr[mid][1] < val):
            return self.binary_insert(arr, mid + 1, high, val)
        elif arr[mid][1] > val:
            return self.binary_insert(arr, low, mid - 1, val)
        else:
            return mid + 1

    def get_encodings(self, node, encode_dict, code):
        if isinstance(node[0], int):
            encode_dict[node[0]] = code
            return

        self.get_encodings(node[0][0], encode_dict, code + "0")
        self.get_encodings(node[0][1], encode_dict, code + "1")
        
    def Huffman_compress(self, DCTs):
        freq = {}
        list_tree = []
            
        for dct in DCTs:
            for num in dct:
                if not num in freq:
                    freq[num] = 0
                freq[num] += 1

        for key, count in freq.items():
            list_tree.append((key, count))

        list_tree.sort(key = lambda count:count[1])

        while len(list_tree) != 1:
            left = list_tree.pop(0)
            right = list_tree.pop(0)
            new_node = ((left, right), left[1] + right[1])
            index = self.binary_insert(list_tree, 0, len(list_tree)-1,new_node[1])
            list_tree.insert(index, new_node)

        encode_dict = {}

        self.get_encodings(list_tree[0], encode_dict, "")

        binary_string = ""
        
        for dct in DCTs:
            for num in dct:
                binary_string = binary_string + encode_dict[num]

        padding = 0
        while (len(binary_string) % 8 != 0):
            binary_string = binary_string + "0"
            padding += 1
            
        self.encode_dict = encode_dict
        
        return binary_string, encode_dict

    def decode_Huffman(self, seq, encode_dict, height, width):
        dct_matrices = [[],[],[]]

        seq_index = 0
        for i in range(3):
            
            for j in range(width*height):
                sub_binary = ""
                while not sub_binary in encode_dict:
                    sub_binary += seq[seq_index]
                    seq_index += 1
                    
                dct_matrices[i].append(encode_dict[sub_binary])
        
        y_new = self.DCT_inverse_transform(dct_matrices[0], width, height, 0)
        u_new = self.DCT_inverse_transform(dct_matrices[1], width, height, 1)
        v_new = self.DCT_inverse_transform(dct_matrices[2], width, height, 1)

        return y_new, u_new, v_new

            
