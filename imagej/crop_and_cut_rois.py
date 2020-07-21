#@ ImagePlus(label="Input Image") imp
#@ File out_dir (label="Output directory", style="directory")
#@ String (visibility=MESSAGE, value="<html><b>Split and cut ROIs for CellPose</b></html>") msg1
#@ String (visibility=MESSAGE, value="Channels will be split and files for each ROI in RoiManager will be saved as tif") msg2
#@ String (visibility=MESSAGE, value="<html><b>Mapping of filters from CZI metadata</b><br/><ol><li>Hoechst 33342 &nbsp;: blue</li><li>Alexa Fluor 488 : green</li><li>Alexa Fluor 594 : red</li><li>Alexa Fluor 647 : yellow</li></ol></html>") msg3
#@ boolean (value=false, label="Copy CellPose run command to clipboard") run_cp
__author__ = "christoph.sommer@ist.ac.at"

# imports
import os
import sys
 
from ij import IJ, WindowManager as wm
from ij.plugin.frame import RoiManager
from ij.plugin import Duplicator, ChannelSplitter

CHANNEL_TO_COLOR = {
    "Alexa Fluor 488" : "green",
    "Hoechst 33342"   : "blue",
    "Alexa Fluor 647" : "yellow",
    "Alexa Fluor 594" : "red"
}

CELLPOSE_CMD_TEMP = "python -m cellpose --dir {} --img_filter blue --use_gpu --pretrained_model cyto --diameter 18"

# functions

def get_original_fileinfo(imp):
    fn = imp.getProp("Location")
    fn_dir  = os.path.dirname(fn)
    fn_base = os.path.basename(fn)
    fn_base, fn_ext  = os.path.splitext(fn_base)
    return fn_dir, fn_base, fn_ext
    
def get_channel_colors(imp):
    channel_color = {}
    for c in range(1, imp.getNChannels()+1):
        c_info = imp.getProp("Information|Image|Channel|Fluor #{}".format(c))
        if c_info in CHANNEL_TO_COLOR:
            print(c, "is", CHANNEL_TO_COLOR[c_info])
            channel_color[c] = CHANNEL_TO_COLOR[c_info]
    return channel_color

def get_roi_images(imp):
    rm = RoiManager.getInstance()
    if not rm:
        IJ.showMessage("Add ROIs to RoiManager first")
        return
        
    rois = list(RoiManager.getInstance().getRoisAsArray())
    res = []
    for roi in rois:
        imp.setRoi(roi)
        roi_img = Duplicator().run(imp, 1, imp.getNChannels(), roi.getZPosition(), roi.getZPosition(), 1, 1) 
        local_roi = roi.clone()
        local_roi.setLocation(0,0)
        roi_img.setRoi(local_roi)
        for c in range(1, imp.getNChannels()+1):
            roi_img.getStack().getProcessor(c).fillOutside(local_roi)

        res.append(roi_img)

    return res
  

# main

def main():
    fn_dir, fn_base, fn_ext = get_original_fileinfo(imp)
    
    roi_images = get_roi_images(imp)
    channel_colors = get_channel_colors(imp)

    for r, im in enumerate(roi_images):
        im_channels = ChannelSplitter().split(im)
        for c, ch_img in enumerate(im_channels):
            out_fn = os.path.join(str(out_dir), "{}_ROI_{:02d}_{}.tif".format(fn_base, r, channel_colors[c+1]))
            IJ.saveAs(ch_img, "Tiff", out_fn)
        
    os.system("explorer {}".format(out_dir))

    print(run_cp)
    print(out_dir)
    
    if run_cp:
        import subprocess
        subprocess.Popen(['clip'], stdin=subprocess.PIPE).communicate(CELLPOSE_CMD_TEMP.format(out_dir))


    
if __name__ in ("__main__", "__builtin__"):
    main()
