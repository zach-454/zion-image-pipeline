#@ File    (label = "Input directory", style = "directory") srcFile
#@ File    (label = "Output directory", style = "directory") dstFile
#@ String  (label = "File extension", value=".tif") ext
#@ String  (label = "File name contains", value = "") containString
#@ boolean (label = "Keep directory structure when saving", value = true) keepDirectories

# See also Process_Folder.ijm for a version of this code
# in the ImageJ 1.x macro language.

import os
from ij import IJ, ImagePlus
from ij.plugin.frame import RoiManager
from ij.plugin import ChannelSplitter
from ij.measure import ResultsTable
from ij.gui import ProfilePlot
import csv

csv_labels = ["mean", "std", "median", "min", "max", "mode"];
rt_idx = {"mean": 1, "std": 2, "median": 21, "min": 4, "max": 5, "mode": 3}

def select_ROIs():
	#todo: implement semi-interactive roi selection
	#mark image used for roi definition as target image for registration
    return
    
def register_to_target(target_img):
	#todo: implement affine registration
    return

def run():
  	for root, directories, filenames in os.walk(srcDir):
		filenames.sort();
		for filename in filenames:
			# Check for file extension
			if not filename.endswith(ext):
				continue
      		# Check for file name pattern
			if containString not in filename:
				continue
			process(srcDir, dstDir, root, filename, keepDirectories)

def process(srcDir, dstDir, currentDir, fileName, keepDirectories):
  	# Opening the image
  	#print "Open image file", fileName
  	imp = IJ.openImage(os.path.join(currentDir, fileName))
   
   	# Opening the roi 
	rm = RoiManager.getRoiManager();
	IJ.run("Set Measurements...", "mean standard modal min median redirect=None decimal=3");
	nRois = rm.getCount()
	channels = ChannelSplitter.split(imp);
	nRows = 0

	for r in range(nRois):  #loop spots
		for ch in range(0,3):
			rm.select(r);
			rm.runCommand(channels[ch],"Measure");
		nRows += 3
	rt = ResultsTable.getActiveTable()

	if nRows:
		hdr_line = ["filename", "roi"]
		for label in csv_labels:
			for chan in ["R","G","B"]:
				hdr_line.append(label + "_" + chan)
  		saveDir = currentDir.replace(srcDir, dstDir) if keepDirectories else dstDir
  		if not os.path.exists(saveDir):
			os.makedirs(saveDir)
		with open(os.path.join(saveDir, 'results.csv'), 'a') as f:
			writer = csv.writer(f, delimiter = ',')
			csv_line = [imp.getTitle()]
			for row in range(0,nRows,3):
				csv_line = [imp.getTitle(), str("spot_"+str(1+row//3).zfill(3))] #it's really an roi_idx here
				for label in csv_labels:
					csv_line += [rt.getStringValue(rt_idx[label], row), rt.getStringValue(rt_idx[label], row+1), rt.getStringValue(rt_idx[label], row+2)]
				print "Appending with line:", csv_line
				writer.writerow(csv_line)
			rt.deleteRows(0, nRows)
 	imp.close()
 	
#Start main script here. Please note that the script DOES require all ROIs to be defined in ROI manager first! This will be relaxed once the roi selection and registration are performed at the start of this script.
srcDir = srcFile.getAbsolutePath()
dstDir = dstFile.getAbsolutePath()

saveDir = currentDir.replace(srcDir, dstDir) if keepDirectories else dstDir
if not os.path.exists(saveDir):
	os.makedirs(saveDir)
print "Saving to", saveDir

hdr_line = ["filename", "roi"]
for label in csv_labels:
	for chan in ["R","G","B"]:
		hdr_line.append(label + "_" + chan)
		
with open(os.path.join(saveDir, 'results.csv'), 'w') as f:
	writer = csv.writer(f, delimiter = ', ') #added space for readability purposes
	writer.writerow(hdr_line)

run()