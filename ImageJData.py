# -*- coding: utf-8 -*-
"""
Created on Tue Nov  1 21:01:42 2022

python module that contains tools for importing spot data extracted by imagej

@author: ZacharyAugenfeld
"""

import os
import itertools
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

csv_cols = ["filename",
            "roi",
            "mean_R",
            "mean_G",
            "mean_B",
            "median_R",
            "median_G",
            "median_B",
            "mode_R",
            "mode_G",
            "mode_B",
            "std_R",
            "std_G",
            "std_B",
            "min_R",
            "max_R",
            "min_G",
            "max_G",
            "min_B",
            "max_B"
            ]

csv_dtypes = 2*['str']+(len(csv_cols)-2)*[np.float32]
bg_spot = "bg"

# %%

def imagej_to_pandas(parent_dir:str, numCycles:int=5, bgSubtract:bool=True, out_file:str=None, exclusions:list=None, gt_data=None):
    
    """
    parent_dir: directory which contains all sub-directories that have been processed by the ImageJ spot extraction batch process
    numCycles: number of cycles
    bgSubtract: whether to background subtract or not (should be labeled as bg in roi name from ImageJ)
    out_file: If not None, where to save csv containing all (pre-basecalled) data
    exclusions: list of any spots that should be removed from dataframe (eg if you know one is extra noisy)
    gt_data: ground truth data to include as columns in dataframe
    
    """
    
    df_total = pd.DataFrame(columns=csv_cols)
    lstNumSpots = []
    
    #TODO: adjust this depending on what are data/cycle dir structure is
    cycle_dirs = ["cycle"+str(cycle+1) for cycle in range(numCycles)]
    subdirs = []
    for cycle_dir in cycle_dirs:
        subdirs += [os.path.join(parent_dir, cycle_dir, "vis"), os.path.join(parent_dir, cycle_dir, "uv")]
    # Note: with this data, UV data is one cycle shorter. So remove last uv cycle:
    subdirs = subdirs[:-1]
    
    for subdir in subdirs:
        filename = os.path.join(parent_dir, subdir, "results.csv")    
        df = pd.read_csv(filename,dtype={col:dtype for col, dtype in zip(csv_cols, csv_dtypes)})
        df = df[csv_cols]
        df.sort_values(["filename", "roi"], inplace=True, ignore_index=True)
        lstNumSpots.append(df["roi"].nunique())
        
        #Note: dependent on directories being called "______n" with n being cycle number
        df = pd.concat([df, pd.Series(name="cycle", data=int(os.path.abspath(os.path.join(subdir, os.pardir))[-1]), dtype=np.uint, index=df.index)], axis=1)
        
        if bgSubtract:
            df1 = pd.DataFrame(columns=csv_cols[2:])
            for idx in range(0,len(df.index), lstNumSpots[-1]):
                bg = df.iloc[idx][["mean_R", "mean_G", "mean_B"]]
                spots = df[(idx+1):(idx+lstNumSpots[-1])]
                df1 = pd.concat([df1, pd.concat([spots["cycle"],
                                                 spots[["mean_R", "median_R", "mode_R", "min_R", "max_R"]]-bg["mean_R"],
                                                 spots[["mean_G", "median_G", "mode_G", "min_G", "max_G"]]-bg["mean_G"],
                                                 spots[["mean_B", "median_B", "mode_B", "min_B", "max_B"]]-bg["mean_B"],
                                                 spots[["std_R", "std_G", "std_B"]], #bias doesn't affect variance/std
                                                 ], axis=1)
                                 ], axis=0)
            df_total = pd.concat([df_total, pd.concat([df[csv_cols[:2]],df1], axis=1).dropna()], axis=0)
            lstNumSpots[-1] -= 1
        else:
            df_total = pd.concat([df_total, df], axis=0)

    # Parse wavelengths and add to data:
    #print(df_total.dtypes)
    wavelengths = [fn.split('_')[-2] for fn in df_total["filename"].to_list()]
    df_total.insert(2, "wavelength", wavelengths)
    wavelengths = sorted(list(set(wavelengths)))
    
    # Now clean up dataframe by removing filenames and sorting
    df_total.drop(labels="filename", axis=1, inplace=True)
    df_total = df_total.astype({"cycle": np.uint})
    df_total.set_index(["roi", "cycle", "wavelength"], inplace=True)
    df_total = df_total.unstack()
    # Now sort columns correctly
    w_idx = []
    for w in wavelengths:
        w_idx += 3*[w]
    ch_idx = []
    # Note: dependent on csv_cols def above
    for c in range(2, 20, 3):
        ch_idx += len(wavelengths) * csv_cols[c:(c+3)]
    mi = pd.MultiIndex.from_arrays([ch_idx, 6*w_idx])
    df_total = df_total.reindex(columns=mi)     
    

    if gt_data:
        gt_bases = pd.Series( data=gt_data, index = df_total.index, name="GT Base")
        df_total = pd.concat([df_total, gt_bases], axis=1)
        
    if exclusions:
        df_total.drop(exclusions, axis=0, level=0, inplace=True)
        
    if out_file:
        df_total.to_csv(os.path.join(parent_dir, out_file))
    
    return df_total
