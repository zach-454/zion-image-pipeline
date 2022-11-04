# -*- coding: utf-8 -*-
"""
Created on Thu Oct 27 10:27:39 2022

@author: ZacharyAugenfeld
"""
import sys, os, glob
import numpy as np
from tifffile import imread, imwrite


# %%
input_color_amts = dict()
output_color_amts = dict()
"""
The following section is for parameters of the psuedo-color definition.

"""

input_color_amts["450"]  = (  0,   0, 2) #ie pick Blue channel from 450-excitation image
input_color_amts["529"]  = (0.5, 0.5, 0)
input_color_amts["590"]  = (0.5, 0.5, 0)
input_color_amts["645"]  = (  1,   0, 0) #ie pick Red channel from 645-excitation image

output_color_amts["450"] = (  0,   0, 1) #ie Blue
output_color_amts["529"] = (  0, 0.5, 0) #ie Greem
output_color_amts["590"] = (0.5, 0.5, 0) #ie Yellow
output_color_amts["645"] = (0.5,   0, 0) #ie Red

excitations = sorted(list(input_color_amts.keys()))
excitations_check = sorted(list(output_color_amts.keys()))
if not excitations == excitations_check:
    raise ValueError("Need definitions for all wavelength excitations!")

N = len(excitations)

if __name__ == "__main__":

    if len(sys.argv)<2:
        raise Exception("No target directory given!")

    if len(sys.argv)<3:
        raise Exception("No output file name given!")

    target_dir = sys.argv[1]
    output_filename = sys.argv[2]

    target_dir = os.path.realpath(target_dir)
    print("Working in directory " + target_dir)

    if not os.path.exists(target_dir):
        raise ValueError(f"{target_dir} does not exist!")

    # Input images into X, a 4-D array:
    tiff_filelist = glob.glob(target_dir+'/*.tiff')
    if not tiff_filelist:
        raise ValueError(f"No .tiff files in given directory!")

    for file_idx, tiff_file in enumerate(tiff_filelist):
        file_wavelength = tiff_file.split('_')[-2]
        if not file_wavelength in excitations:
            raise ValueError(f"No entry in I/O amounts for provided excitation wavelength {file_wavelength} in file {tiff_file}")
        else:
            w_idx = excitations.index(file_wavelength)
            img = imread(tiff_file)
            if not file_idx: #is this the first image load
                X = np.zeros(shape=img.shape+(N,), dtype=np.uint16)
            X[:,:,:,w_idx] = img

    # Create numpy matrix from input_color_amts:
    A = np.zeros(shape=(3, N), dtype=float)
    for wavelength, in_amt in input_color_amts.items():
        A[:, excitations.index(wavelength)] = np.array(in_amt)

    # Create numpy matrix from output_color_amts:
    B = np.zeros(shape=(N, 3), dtype=float)
    for wavelength, out_amt in output_color_amts.items():
        B[excitations.index(wavelength), :] = np.array(out_amt)

    # create hidden variable Z which contains 4 monochrome images, all summed from input image channels according to A
    Z = np.einsum('ijkl,kl->ijl', X, A)
    
    if False: #for debugging
        for w_idx, wavelength in enumerate(excitations):
            img_to_save = np.round_(Z[:,:,w_idx]).astype(np.uint16)
            imwrite(os.path.join(target_dir, output_filename+"_"+wavelength+".tif"), img_to_save)

    # output image is simply the matrix multiplication of Z and B
    Y = Z @ B
    print(np.linalg.norm(Y-np.round_(Y)))
    Y_int = np.round_(Y).astype(np.uint16)

    imwrite(os.path.join(target_dir, output_filename), Y_int, photometric='rgb')
    print("Wrote file "+os.path.join(target_dir, output_filename))