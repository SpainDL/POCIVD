#!/usr/bin/env python3

# Note that __SCRIPTNAME__ will be replaced with the actual script name when the script
# is run

"""
pyClarity Generated Script : __SCRIPTNAME__ [help or ?] [prtout] [loop=loop] [profile[=file]]

Parameters:
    loop=N:             number of loops to perform (default is 1, 0 is run continously)
    prtout[=0|1]:       / the output of the process function on each loop. This is
                        the default when the script is run stand-alone, use "prtout=0"
                        to suppress this.
    profile[=filename]: profile the script and show the results in the console
                        or save the results to filename
    help (or ?):        o this help
"""
#JDK_XJPRO_DOC: pyClarity Generated Solution

### imports ####

import sys
import os
import platform
import pathlib
from jlog import jlog
import json
import re
import enum
import json
import os
from typing import Any, Optional
import cv2
from acquire import AcquireInstance, AcquisitionMode, AnalogGain, AutoExposureSettings, ExposureMode, RegionOfInterest, get_active_camera
from jlog import log
from pyclarity_element_core.connectors import Input, Output
from pyclarity_element_core.cvImage import ImageFormat, cvImage
from pyclarity_element_core.element import OFFLINE_MODE, RUN_ONCE, Element
from pyclarity_element_core.Errors import LoopTerminationException
from pyclarity_element_core.ImageHelper import CamToImg
from pyclarity_element_core.parameters import AcquireConfigParam, BoolParam, ComboBoxParam, IntParam, Param, PathParam, ViewerParam
from pyclarity_element_core.ImageHelper import CamToImg, GetSlices, GetOfflineImage
import mvlib
from mvlib import utils as ut
from pyclarity_element_core.element import Element
from pyclarity_element_core.parameters import *
from pyclarity_element_core.cvImage import cvImage
from mvlib import utils
from time import time
import acquire
import numpy as np
from pyclarity_element_core.element import RUN_ONCE, Element
from pyclarity_element_core.ImageHelper import ConvertImage, ImageOutputs
from pprint import pprint
from pyclarity_element_core.graph import Graph
from pyclarity_element_core.ScriptUtils import HandleMessages, err_print, ScriptContext, ScriptMessage
from pyclarity_element_core.Errors import LoopTerminationException
from pyclarity_element_core.element import RUN_ONCE
from pyclarity_element_core.utils import ElemType
from acquire import set_active_camera

__SCRIPTNAME__ = os.path.basename(os.path.splitext(__file__)[0])
__doc__ = __doc__.replace("__SCRIPTNAME__", __SCRIPTNAME__).rstrip()

SCRIPT = __file__
ASSETDIR = os.path.splitext(__file__)[0] + '_assets'

LOG_TO_CONSOLE = False
LOG_FILE_LEVEL = jlog.DEBUG  #jlog.DEBUG, jlog.INFO, jlog.WARNING, jog.ERROR, jlog.FATAL
LOG_CONSOLE_LEVEL = jlog.DEBUG  #jlog.DEBUG, jlog.INFO, jlog.WARNING, jog.ERROR, jlog.FATAL

def StrToBool(s):
    return s.lower() in ("true", "t", "yes", "y", 1)

#setup logger before any global function call
def setup_logger(log_to_console, file_log_level, console_log_level):
    jlog.createFileHandler(pathlib.Path(__file__).stem)
    jlog.setFileLoggingLevel(file_log_level)

    if log_to_console:
        jlog.enable_console_logger()
        jlog.setStreamLoggingLevel(console_log_level)
        
setup_logger(LOG_TO_CONSOLE, LOG_FILE_LEVEL, LOG_CONSOLE_LEVEL)

# Return the asset if it exists
def __filename(f):
    if not f:
        f = __file__  # Running in a script
    z = re.split(r'[\\/:]', f)
    k = len(z)
    while k > 0:
        if z[k-1]:
            return z[k-1]
        k -= 1

def get_asset(filename):
    name = __filename(filename)
    asset = os.path.join(ASSETDIR, name)
    if os.path.exists(asset):
        return asset
    if os.path.exists(filename):
        return filename
    return ''

# Return the path to an asset in the asset folder, whether it exists or not
def get_asset_path(filename):
    name = __filename(filename)
    asset = os.path.join(ASSETDIR, name)
    return asset

class ObjectManager():

    def __init__(self, obj):
        self._obj = obj
        self.initialize()

    def obj(self):
        return self._obj

    def initialize(self):
        pass

### Module Classes ###

class acquireImageCamera(ObjectManager):

    class acquireImageCamera(Element):
        """This element is primary element for capturing images from camera due to the fact that it supports streaming images.
    
        Steaming images is video like capture means that runs in the background and makes new images available to consumer (like
        this element) in frame time (+ any host interface physical interface transmission delays).  In this way it is characteristically
        different than snapImage elements.  The primary implementation difference is that snapImage elements perform full capture sequence
        every time in the processScript(), where full process is stream_start(), stream_get() and stream_stop().  Conversely, acquireImage
        elements do stream_start() on preProcess(), stream_get() in the processScript(), and stream_stop() in the postProcess().  The result
        is a more efficient stream video concept most appreciable running graphs and/or generated scripts in loops or continuous mode.  As
        such, the acquireImage elements are better aligned with AcquisitionMode = Continuous, where snapImage elements are more aligned with
        AcquisitionMode = MultiFrame or SingleFrame modes.  This element also supports capturing images from files and folders per OFFLINE mode.
    
        Inputs:
            sync: optional input intended to allow for control execution flow.
    
        Outputs:
            img (cvImage): output image captured or open via file
            offset: intended to be x,y offset anchor into the individual image for future elements, currently just a placeholder.
            img_name: filename in the OFFLINE use mode, "camera" when capturing from the camera.
    
    
        Parameters:
            view (ViewerParam): boolean select to hide/show external image viewer when this element is run as a graphical node
            acqConf (AcquireConfigParam): Genicam based configuration parameter associated with how the camera is configured
                to capture images.
            imageFormat (ComboBoxParam): parameter to select the cvImage ImageFormat associated with the output["img"] of this element.
                Note this is unique from the captured image format which is defined by acqConf "PixelFormat".
                Note also if "PixelFormat" and imageFormat are different, the element(node) is the one
                applying the implied interpolation to achieve the output format.
            Index (IntParam): index counter used mostly to reference to files in case you are recursing through a folder, etc
            path (PathParam): reference path to image file or folder where images exist.  Means by which img input is satisfied ONLY
                when if acqConf is OFFLINE.
            loop (BoolParam): enable if user wants to continously run against a given folder.  Like path, this is only meaningful
                if acqConf is OFFLINE.
        """
    
        _name = "Acquire Image from Camera"
        _comment = "This node acquires images from the camera and supports streaming"
    
        def attributes(self) -> tuple[list[Input], list[Output], list[Param]]:
            return (
                [Input("sync")],
                [Output("img"), Output("offset"), Output("img_name")],
                [
                    ViewerParam("view"),
                    AcquireConfigParam(
                        "acqConf",
                        instance_creator=lambda name=None: AcquireInstance(
                            name or get_active_camera() or OFFLINE_MODE
                        ),
                    ),
                    ComboBoxParam(
                        "imageFormat",
                        values={
                            "Raw Bayer": ImageFormat.Bayer_GB,
                            # Just select one of the Bayer formats for now, we'll get it working right with genicam support
                            "Mono": ImageFormat.Mono,
                            "RGB": ImageFormat.RGB,
                            "BGR": ImageFormat.BGR,
                        },
                        defaultVal=ImageFormat.Mono,
                        display="cvImage Image Format",
                    ),
                    PathParam("cam_cfg", display="Camera config file", runOnce=True),
                    IntParam("Index", value=0),
                    PathParam("path", display="Image File"),
                    BoolParam("loop", display="Continuous Loop"),
                ],
            )
    
        def getCameraImage(
            self, preInit: dict[str, Any], params: dict[str, Any]
        ) -> cvImage:
            img = CamToImg(
                params["acqConf"].get_instance().stream_get(), params["imageFormat"].get()
            )
    
            # imperfect but here to support exposure calibration
            img.meta()["led_power"] = params["acqConf"]["IllumValue"]
            img.meta()["exposure_mode"] = params["acqConf"]["ExposureAuto"]
            img.meta()["analog_gain"] = params["acqConf"]["AnalogGain"]
            log.debug(f"Image capture timestamp: {img.meta().get('timestamp_ms', None)}")
            log.info(f"Metadata: {img.meta()}")
    
            return img
    
        def processScript(
            self,
            inputs: dict[str, Any],
            outputs: dict[str, Any],
            params: dict[str, Any],
            preInit: dict[str, Any],
        ) -> None:
            if params["acqConf"].get_instance() is None:
                try:
                    outputs["img"], outputs["img_name"], idx = GetOfflineImage(
                        params["path"].get(),
                        params["Index"].get(),
                        params["loop"].get(),
                        params["imageFormat"].get(),
                    )
                    params["Index"].set(idx)
                    params["view"].appendTitle(": " + outputs["img_name"])
                except:
                    params["Index"].set(0)
                    raise
    
            else:
                if "offset" in preInit:
                    outputs["offset"] = preInit["offset"]
    
                outputs["img"] = self.getCameraImage(preInit, params)
                outputs["img_name"] = None
    
            params["view"].updateImage(outputs["img"])
    
        def init(self, params: dict[str, Any]) -> Optional[Any]:
            if params["acqConf"].get_instance() is None:
                return None
    
            if params["cam_cfg"].get():
                with open(params["cam_cfg"].get(), "r") as f:
                    cfg_dict = json.loads(f.read())
                for cfg in cfg_dict:
                    params["acqConf"].__setitem__(cfg, cfg_dict[cfg])
    
            return None
    
        def preProcess(self, params: dict[str, Any], preInit: dict[str, Any]) -> None:
            if params["acqConf"].get_instance() is None:
                return
    
            params["acqConf"].get_instance().stream_start()
    
        def postProcess(self, params: dict[str, Any], preInit: dict[str, Any]) -> None:
            if params["acqConf"].get_instance() is None:
                return
    
            params["acqConf"].get_instance().stream_stop()
            params["acqConf"].drop_instance()
    
    
    def __init__(self):
        super().__init__(acquireImageCamera.acquireImageCamera())

    def initialize(self):
        self.obj().name = "acquireImageCamera"
        set_active_camera("9999999 U3V (JADAK - A Novanta Company-2978D00F9999999-9999999)")
        
        for param in self.obj().params.values():
        
            if param.name == "acqConf":
                param.set({
                    "Width": 2592,
                    "Height": 1944,
                    "OffsetX": 0,
                    "OffsetY": 0,
                    "ReverseX": False,
                    "ReverseY": False,
                    "PixelFormat": 17301505,
                    "BinningHorizontal": 1,
                    "BinningVertical": 1,
                    "AcquisitionMode": 0,
                    "AcquisitionFrameCount": 3,
                    "AcquisitionFrameTime": 0,
                    "ExposureTime": 1750.0,
                    "ExposureAuto": 0,
                    "IllumEnable": 0,
                    "IllumValue": 0,
                    "FilterLibrary": "",
                    "AnalogGain": 1,
                    "BalanceWhiteAuto": 0,
                    "ChunkModeActive": True,
                    "ChunkSelector": 12,
                    "ChunkEnable": True,
                    "BayerConvAlg": 2,
                    "GPIOPin": 0,
                    "GPIOValue": 0,
                    "ae_log": 0,
                    "ae_target": 160,
                    "ae_tolerance": 5,
                    "ae_RowSkip": 6,
                    "ae_PixSkip": 6,
                    "ae_FrameSkip": 2,
                    "ae_ExpMin": 100,
                    "ae_ExpMax": 880000,
                    "ae_startExp": 15000,
                    "ae_targetPercentile": 95,
                    "ae_conformanceTries": 1,
                    "ae_ExpRoiEnable": False,
                    "ae_ExpRoiLeft": 0,
                    "ae_ExpRoiTop": 0,
                    "ae_ExpRoiWidth": 2592,
                    "ae_ExpRoiHeight": 1944,
                    "ae_ReapplyStartingExposure": False,
                    "ae_RememberedExposureFloor": 100,
                    "ae_RememberedExposureCeiling": 200000,
                    "ae_BayerSampleMode": 2
                })
            
            elif param.name == "imageFormat":
                param.set(4)
            
            elif param.name == "cam_cfg":
                param.set(get_asset(""))
            
            elif param.name == "Index":
                param.set(0)
            
            elif param.name == "path":
                param.set(get_asset(""))
            
            elif param.name == "loop":
                param.set(False)
            
class featureFind(ObjectManager):

    class featureFind(Element):
        """
        Given an input image, and optional offset, angle or roi,
        try to find a pattern or edge using trained data.
        
        :param inputs["img"]:   Input color or mono image.
        :type inputs["img"]:    numpy array
        :param inputs["offset"]:   Optional input offset and angle.
        :type inputs["offset"]:    dict = {"x": xoffset, "y": yoffset, "angle": angle}
        :param inputs["search_roi"]:   Optional input search roi.
        :type inputs["search_roi"]:    dict = {"x": xoffset, "y": yoffset, "width": roi_width, "height": roi_height} 
        
        :param outputs["results"]:    Output struct from C++ function.
        :type outputs["results"]:     DotMap object = (return_val, found, found_offset, score, found_center_point, draw_images)
        :param outputs["found"]:    Output found pattern / feature or not.
        :type outputs["found"]:     boolean
        :param outputs["score"]:    Output matching score.
        :type outputs["score"]:     int
        :param outputs["center_point"]:    Output center point.
        :type outputs["center_point"]:     dict = {"x": center_x, "y": center_y} 
    
        :param params["view"]:   Embedded viewer to display the image with results.
        :type params["view"]:    ViewerParam object
        :param params["Pattern"]:   Pre-trained pattern binary file name
        :type params["Pattern"]:    PathParam object
        :param params["roi"]:       Let user select roi if not from inputs.
        :type params["roi"]:        RoiParam object
        :param params["TrainFeatureFind"]:   Optionally load TrainingParam GUI to do training to generate pattern binary data file.
        :type params["TrainFeatureFind"]:    TrainingParam object
    
        :param params["AnchorOffset_X"]:   X offset of anchor point.
        :type params["AnchorOffset_X"]:    IntParam
        :param params["AnchorOffset_Y"]:   Y offset of anchor point.
        :type params["AnchorOffset_Y"]:    IntParam
    
        :param params["Low_Res_Threshold"]:   Low threshold.
        :type params["Low_Res_Threshold"]:    IntParam
        :param params["High_Res_Threshold"]:   High threshold.
        :type params["High_Res_Threshold"]:    IntParam
    
        :param params["Min_Angle"]:   Minimum angle.
        :type params["Min_Angle"]:    IntParam
        :param params["Max_Angle"]:   Maximum angle.
        :type params["Max_Angle"]:    IntParam
    
        :param params["Required_Score_(0-100)"]:   Required score for a good detection.
        :type params["Required_Score_(0-100)"]:    IntParam
        :param params["Trans_Skip"]:   Pixel values to skip detection.
        :type params["Trans_Skip"]:    IntParam
    
        :param params["Max_Iterations"]:   Number of iterations to try.
        :type params["Max_Iterations"]:    IntParam
    
        :param params["Coarse_Angle_Step"]:   Angle step to search in coarse pass.
        :type params["Coarse_Angle_Step"]:    IntParam
        :param params["Fine_Angle_Step"]:   Angle step to search in refined pass.
        :type params["Fine_Angle_Step"]:    IntParam
         
        """
    
        _name = "FeatureFind"
        _comment = "Finds a Pattern or detects an Edge in a scene"
    
        def attributes(self):
            return (
                [Input("img"), Input("offset"), Input("search roi")],
                [
                    Output("result"),
                    Output("found"),
                    Output("score"),
                    Output("center point"),
                ],
                [
                    ViewerParam("view"),
                    PathParam("Pattern", associate="TrainFeatureFind"),
                    IntParam("AnchorOffset_X", value=0),
                    IntParam("AnchorOffset_Y", value=0),
                    IntParam("Low Res Threshold", value=0, minVal=0, maxVal=255),
                    IntParam("High Res Threshold", value=100, minVal=0, maxVal=255),
                    IntParam("Min Angle", value=-25, minVal=-180, maxVal=0),
                    IntParam("Max Angle", value=25, minVal=0, maxVal=180),
                    IntParam("Required Score (0-100)", value=90, minVal=0, maxVal=100),
                    IntParam("Trans Skip", value=5, minVal=0, maxVal=255),
                    IntParam("Max Iterations", value=5, minVal=0, maxVal=100),
                    IntParam("Coarse Angle Step", value=4, minVal=0, maxVal=100),
                    IntParam("Fine Angle Step", value=1, minVal=0, maxVal=100),
                    RoiParam("roi", viewerTag="view", alwaysOn=True),
                    TrainingParam(
                        "TrainFeatureFind",
                        None,
                        trainingType="feature find",
                        display="Train Feature Find Pattern",
                    ),
                ],
            )
    
        def processScript(self, inputs, outputs, params, preInit):
            if "img" not in inputs:
                raise Exception("Missing input image")
            if isinstance(inputs["img"], cvImage):
                img = inputs["img"]
            else:
                try:
                    img = cvImage(inputs["img"])
                except:
                    raise Exception("Unsupport image format")
    
            params["TrainFeatureFind"].setImageForTraining(img)
            if not params["Pattern"].get():
                raise Exception("Must supply pattern file name")
    
            finder = mvlib.FeatureFind(
                pattern=ut.read_binary_file(params["Pattern"].get()),
                low_res_thresh=params["Low Res Threshold"].get(),
                high_res_thresh=params["High Res Threshold"].get(),
                min_angle=params["Min Angle"].get(),
                max_angle=params["Max Angle"].get(),
                reqd_score=params["Required Score (0-100)"].get(),
                trans_skip=params["Trans Skip"].get(),
                max_iter=params["Max Iterations"].get(),
                coarse_angle_step=params["Coarse Angle Step"].get(),
                find_angle_step=params["Fine Angle Step"].get(),
            )
    
            # Input ROI has priority
            rect = None
            if "search roi" in inputs:
                params["roi"].setEnabled(False)
                rect = inputs["search roi"]
                finder.set_roi(rect["x"], rect["y"], rect["width"], rect["height"])
            elif params["roi"].isEnabled():
                rect = params["roi"].getRect()
                finder.set_roi(rect["x"], rect["y"], rect["width"], rect["height"])
            else:
                finder.roi = None
    
            if "offset" in inputs:
                if "angle" in inputs["offset"]:
                    angle = inputs["offset"]["angle"]
                else:
                    angle = 0
                finder.set_offset(
                    inputs["offset"]["x"], inputs["offset"]["y"], inputs["offset"]["angle"]
                )
    
            outputs["result"] = finder.find(img)
    
            # If library output a marked up image and it was found, display it - otherwise use the input image
            if outputs["result"].draw_images and outputs["result"].found:
                params["view"].updateImage(outputs["result"].draw_images[0])
            else:
                params["view"].updateImage(img)
    
            RED = 0xFF0000
            GREEN = 0xFF00
            if outputs["result"].return_val != 0:
                if params["roi"].isEnabled():
                    params["roi"].setColor(RED)
                else:
                    params["view"].AddRect(
                        outputs["roi"]["x"],
                        outputs["roi"]["y"],
                        outputs["roi"]["width"],
                        outputs["roi"]["height"],
                        color=RED,
                    )
                    outputs["found"] = 0
                    outputs["score"] = 0
                    outputs["center point"] = {"x": 0, "y": 0}
    
                raise Exception(
                    "Feature Find failed with return value: "
                    + ut.script_result_to_string(outputs["result"].return_val)
                )
            else:
                if outputs["result"].found:
                    if params["roi"].isEnabled():
                        params["roi"].setColor(GREEN)
                    elif rect:
                        params["view"].AddRect(
                            rect["x"], rect["y"], rect["width"], rect["height"], color=GREEN
                        )
                        params["view"].DrawAddedObjects()
                else:
                    if params["roi"].isEnabled():
                        params["roi"].setColor(RED)
                    elif rect:
                        params["view"].AddRect(
                            rect["x"], rect["y"], rect["width"], rect["height"], color=RED
                        )
                        params["view"].DrawAddedObjects()
    
                outputs["found"] = outputs["result"].found
                outputs["score"] = outputs["result"].score
                outputs["center point"] = {
                    "x": outputs["result"].found_offset.ul.x,
                    "y": outputs["result"].found_offset.ul.y,
                }
    
                params["view"].AddText(
                    "Score: " + str(outputs["result"].score),
                    rect["x"] + 5 if rect else outputs["center point"]["x"],
                    rect["y"] if rect else outputs["center point"]["y"],
                    35,
                    0x0000FF,
                )
                params["view"].DrawAddedObjects()
    
                log.info("Found: " + str(outputs["result"].found))
                log.info("Score: " + str(outputs["result"].score))
                log.info(
                    "Found Offset: {}, {}".format(
                        outputs["result"].found_offset.ul.x,
                        outputs["result"].found_offset.ul.y,
                    )
                )
                log.info(
                    "Found Center: {}, {}".format(
                        outputs["result"].found_center_point.x,
                        outputs["result"].found_center_point.y,
                    )
                )
    
    
    def __init__(self):
        super().__init__(featureFind.featureFind())

    def initialize(self):
        self.obj().name = "featureFind"
        for param in self.obj().params.values():
        
            if param.name == "Pattern":
                param.set(get_asset("C:/ClarityStudio Alpha/v6.02/pyClarityData/userspace/assets/pix_pattern_2023_06_26__11_17_45_AM.bin"))
            
            elif param.name == "AnchorOffset_X":
                param.set(0)
            
            elif param.name == "AnchorOffset_Y":
                param.set(-5)
            
            elif param.name == "Low Res Threshold":
                param.set(0)
            
            elif param.name == "High Res Threshold":
                param.set(100)
            
            elif param.name == "Min Angle":
                param.set(-25)
            
            elif param.name == "Max Angle":
                param.set(25)
            
            elif param.name == "Required Score (0-100)":
                param.set(90)
            
            elif param.name == "Trans Skip":
                param.set(5)
            
            elif param.name == "Max Iterations":
                param.set(5)
            
            elif param.name == "Coarse Angle Step":
                param.set(5)
            
            elif param.name == "Fine Angle Step":
                param.set(1)
            
            elif param.name == "roi":
                param.set({
                    "x": 1100,
                    "y": 1053,
                    "width": 766,
                    "height": 152,
                    "angle": 0
                })
                param.setEnabled(True)
            
class RoiFromCenterPoint(ObjectManager):

    class RoiFromCenterPoint(Element):
        """
        This Element, named "ROI generation from center point", is designed to generate a ROI based on an input center point. It takes an image and a center point as inputs, generates a ROI based on the center point, and outputs it.
    
        Inputs:
            img (img): Input image for the element
            center point (dict): Input center point for the element
    
        Outputs:
            roi (dict): Output ROI of the element
    
        Parameters:
            view (ViewerParam): Viewer parameter for the element
            full_width (BoolParam): Boolean parameter indicating whether to use the full width of the image
            full_height (BoolParam): Boolean parameter indicating whether to use the full height of the image
            xoff (IntParam): Column start offset from the center point
            yoff (IntParam): Row start offset from the center point
            width (IntParam): Width of the ROI
            height (IntParam): Height of the ROI
        """
    
        _name = "ROI generation from center point"
        _comment = "Generates a ROI based on input center point"
    
        def attributes(self):
            return (
                [Input("img"), Input("center point")],
                [Output("roi")],
                [
                    ViewerParam("view"),
                    BoolParam("full_width", display="Use full width"),
                    BoolParam("full_height", display="Use full height"),
                    IntParam(
                        "xoff",
                        value=0,
                        display="Column start\n  - offset from center point",
                    ),
                    IntParam(
                        "yoff", value=0, display="Row start\n  - offset from center point"
                    ),
                    IntParam("width", value=100, display="Width of ROI"),
                    IntParam("height", value=100, display="Height of ROI"),
                ],
            )
    
        def processScript(self, inputs, outputs, params, preInit):
            if "center point" not in inputs:
                raise Exception("No center point")
    
            if params["full_width"].get():
                x = 0
                w = inputs["img"].nWidth
            else:
                w = params["width"].get()
                x = inputs["center point"]["x"] - int(w / 2) + params["xoff"].get()
                if x < 0:
                    x = 0
    
            if params["full_height"].get():
                y = 0
                h = inputs["img"].nHeight
            else:
                h = params["height"].get()
                y = inputs["center point"]["y"] - int(h / 2) + params["yoff"].get()
                if y < 0:
                    y = 0
    
            outputs["roi"] = {"x": x, "y": y, "width": w, "height": h}
    
            if "img" in inputs:
                params["view"].updateImage(inputs["img"])
                BLUE = 0x0000FF
                params["view"].AddRect(
                    outputs["roi"]["x"],
                    outputs["roi"]["y"],
                    outputs["roi"]["width"],
                    outputs["roi"]["height"],
                    color=BLUE,
                )
                params["view"].DrawAddedObjects()
    
    
    def __init__(self):
        super().__init__(RoiFromCenterPoint.RoiFromCenterPoint())

    def initialize(self):
        self.obj().name = "RoiFromCenterPoint"
        for param in self.obj().params.values():
        
            if param.name == "full_width":
                param.set(None)
            
            elif param.name == "full_height":
                param.set(None)
            
            elif param.name == "xoff":
                param.set(40)
            
            elif param.name == "yoff":
                param.set(-80)
            
            elif param.name == "width":
                param.set(100)
            
            elif param.name == "height":
                param.set(100)
            
class Control_lineFinder(ObjectManager):

    class Control_lineFinder(Element):
        _name = "MVLIb Line Finder"
        _comment = "Primitive line finder"
    
        def attributes(self):
            return [Input("img"),
                 Input("offset"),
                 Input("search roi")], \
                [Output("result"),
                 Output("found"),
                 Output("score"),
                 Output("center point")], \
                [ViewerParam("view"),
                 IntParam("Min Contrast", value=25, minVal=10, maxVal=240),
                 IntParam("Min Shape", value=30, minVal=10, maxVal=99),
                 IntParam("Max Angle", value=30, minVal=0, maxVal=45),
                 BoolParam("Rotation Allowed", value=True),
                 ComboBoxParam("Polarity",
                               values={"Black to White":mvlib.PRIMITIVE_FIND_POLARITY_BLACK_TO_WHITE,
                                       "White to Black":mvlib.PRIMITIVE_FIND_POLARITY_WHITE_TO_BLACK,
                                       "Both":mvlib.PRIMITIVE_FIND_POLARITY_BOTH}),
                 ComboBoxParam("Find Mode",
                               values={"Strongest":mvlib.PrimitiveFindLine.LINE_STRONGEST,
                                        "Left Most":mvlib.PrimitiveFindLine.LINE_LEFTMOST,
                                        "Mid Most":mvlib.PrimitiveFindLine.LINE_MIDMOST,
                                        "Right Most":mvlib.PrimitiveFindLine.LINE_RIGHTMOST,
                                        "Left Strong":mvlib.PrimitiveFindLine.LINE_LEFTSTRONG,
                                        "Middle Strong":mvlib.PrimitiveFindLine.LINE_MIDDLESTRONG,
                                        "Right Strong":mvlib.PrimitiveFindLine.LINE_RIGHTSTRONG}),
                 RoiParam("roi", viewerTag="view")]
    
        def processScript(self, inputs, outputs, params, preInit):
            if "img" not in inputs:
                raise Exception("No input image")
    
            finder = mvlib.PrimitiveFindLine(polarity=params["Polarity"].get(),
                                min_contrast=params["Min Contrast"].get(),
                                min_shape=params["Min Shape"].get(),
                                find_mode=params["Find Mode"].get(),
                                rot_allowed=params["Rotation Allowed"].get(),
                                max_angle=params["Max Angle"].get())
            
            # Input ROI has priority
            rect = None
            if "search roi" in inputs:
                params["roi"].setEnabled(False)
                rect = inputs["search roi"]
                finder.set_roi(rect["x"], rect["y"], rect["width"], rect["height"])
            elif params["roi"].isEnabled():
                rect = params["roi"].getRect()
                finder.set_roi(rect["x"], rect["y"], rect["width"], rect["height"])
            else:
                finder.roi = None
    
            if "offset" in inputs:
                if "angle" in inputs["offset"]:
                    angle = inputs["offset"]["angle"]
                else:
                    angle = 0
                finder.set_offset(inputs["offset"]["x"],
                                  inputs["offset"]["y"],
                                  angle)
    
            outputs["result"] = finder.find_line(inputs["img"])
    
            RED = 0xff0000
            GREEN = 0xff00
            params["view"].updateImage(inputs["img"])        
            if outputs["result"].return_val != 0:
                if params["roi"].isEnabled():
                    params["roi"].setColor(RED)
                elif rect:
                    params["view"].AddRect(
                            rect["x"],
                            rect["y"],
                            rect["width"],
                            rect["height"], color=RED)
                    params["view"].DrawAddedObjects()
                outputs["found"] = 0
                outputs["score"] = 0
                outputs["center point"] = {
                    "x": 0,
                    "y": 0}
    
                raise Exception("Line Find Failed with return value: " + 
                      mvlib.utils.script_result_to_string(outputs["result"].return_val))
            else:
                if params["roi"].isEnabled():
                    params["roi"].setColor(GREEN)
                elif rect:
                    params["view"].AddRect(
                            rect["x"],
                            rect["y"],
                            rect["width"],
                            rect["height"], color=GREEN)
                params["view"].AddLine(outputs["result"].line_point_a_x,
                                       outputs["result"].line_point_a_y,
                                       outputs["result"].line_point_b_x,
                                       outputs["result"].line_point_b_y,
                                       3,
                                       0x00FF00)  # Green
                params["view"].DrawAddedObjects()
                outputs["found"] = outputs["result"].found
                outputs["score"] = outputs["result"].score
                outputs["center point"] = {
                    "x": outputs["result"].line_midpoint_x,
                    "y": outputs["result"].line_midpoint_y}
    
                log.info("Found: " + str(outputs["found"]))
                log.info("Score: " + str(outputs["score"]))
                log.info("Line Mid Point ({}, {})".format(
                    outputs["result"].line_midpoint_x,
                    outputs["result"].line_midpoint_y))                                             
    
    
    def __init__(self):
        super().__init__(Control_lineFinder.Control_lineFinder())

    def initialize(self):
        self.obj().name = "Control_lineFinder"
        for param in self.obj().params.values():
        
            if param.name == "Min Contrast":
                param.set(25)
            
            elif param.name == "Min Shape":
                param.set(30)
            
            elif param.name == "Max Angle":
                param.set(30)
            
            elif param.name == "Rotation Allowed":
                param.set(False)
            
            elif param.name == "Polarity":
                param.set(2)
            
            elif param.name == "Find Mode":
                param.set(3)
            
            elif param.name == "roi":
                param.set({
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32,
                    "angle": 0
                })
                param.setEnabled(False)
            
class RoiFromCenterPoint1(ObjectManager):

    class RoiFromCenterPoint(Element):
        """
        This Element, named "ROI generation from center point", is designed to generate a ROI based on an input center point. It takes an image and a center point as inputs, generates a ROI based on the center point, and outputs it.
    
        Inputs:
            img (img): Input image for the element
            center point (dict): Input center point for the element
    
        Outputs:
            roi (dict): Output ROI of the element
    
        Parameters:
            view (ViewerParam): Viewer parameter for the element
            full_width (BoolParam): Boolean parameter indicating whether to use the full width of the image
            full_height (BoolParam): Boolean parameter indicating whether to use the full height of the image
            xoff (IntParam): Column start offset from the center point
            yoff (IntParam): Row start offset from the center point
            width (IntParam): Width of the ROI
            height (IntParam): Height of the ROI
        """
    
        _name = "ROI generation from center point"
        _comment = "Generates a ROI based on input center point"
    
        def attributes(self):
            return (
                [Input("img"), Input("center point")],
                [Output("roi")],
                [
                    ViewerParam("view"),
                    BoolParam("full_width", display="Use full width"),
                    BoolParam("full_height", display="Use full height"),
                    IntParam(
                        "xoff",
                        value=0,
                        display="Column start\n  - offset from center point",
                    ),
                    IntParam(
                        "yoff", value=0, display="Row start\n  - offset from center point"
                    ),
                    IntParam("width", value=100, display="Width of ROI"),
                    IntParam("height", value=100, display="Height of ROI"),
                ],
            )
    
        def processScript(self, inputs, outputs, params, preInit):
            if "center point" not in inputs:
                raise Exception("No center point")
    
            if params["full_width"].get():
                x = 0
                w = inputs["img"].nWidth
            else:
                w = params["width"].get()
                x = inputs["center point"]["x"] - int(w / 2) + params["xoff"].get()
                if x < 0:
                    x = 0
    
            if params["full_height"].get():
                y = 0
                h = inputs["img"].nHeight
            else:
                h = params["height"].get()
                y = inputs["center point"]["y"] - int(h / 2) + params["yoff"].get()
                if y < 0:
                    y = 0
    
            outputs["roi"] = {"x": x, "y": y, "width": w, "height": h}
    
            if "img" in inputs:
                params["view"].updateImage(inputs["img"])
                BLUE = 0x0000FF
                params["view"].AddRect(
                    outputs["roi"]["x"],
                    outputs["roi"]["y"],
                    outputs["roi"]["width"],
                    outputs["roi"]["height"],
                    color=BLUE,
                )
                params["view"].DrawAddedObjects()
    
    
    def __init__(self):
        super().__init__(RoiFromCenterPoint1.RoiFromCenterPoint())

    def initialize(self):
        self.obj().name = "RoiFromCenterPoint1"
        for param in self.obj().params.values():
        
            if param.name == "full_width":
                param.set(False)
            
            elif param.name == "full_height":
                param.set(False)
            
            elif param.name == "xoff":
                param.set(150)
            
            elif param.name == "yoff":
                param.set(-80)
            
            elif param.name == "width":
                param.set(100)
            
            elif param.name == "height":
                param.set(100)
            
class Test_lineFinder(ObjectManager):

    class Test_lineFinder(Element):
        _name = "MVLIb Line Finder"
        _comment = "Primitive line finder"
    
        def attributes(self):
            return [Input("img"),
                 Input("offset"),
                 Input("search roi")], \
                [Output("result"),
                 Output("found"),
                 Output("score"),
                 Output("center point")], \
                [ViewerParam("view"),
                 IntParam("Min Contrast", value=25, minVal=10, maxVal=240),
                 IntParam("Min Shape", value=30, minVal=10, maxVal=99),
                 IntParam("Max Angle", value=30, minVal=0, maxVal=45),
                 BoolParam("Rotation Allowed", value=True),
                 ComboBoxParam("Polarity",
                               values={"Black to White":mvlib.PRIMITIVE_FIND_POLARITY_BLACK_TO_WHITE,
                                       "White to Black":mvlib.PRIMITIVE_FIND_POLARITY_WHITE_TO_BLACK,
                                       "Both":mvlib.PRIMITIVE_FIND_POLARITY_BOTH}),
                 ComboBoxParam("Find Mode",
                               values={"Strongest":mvlib.PrimitiveFindLine.LINE_STRONGEST,
                                        "Left Most":mvlib.PrimitiveFindLine.LINE_LEFTMOST,
                                        "Mid Most":mvlib.PrimitiveFindLine.LINE_MIDMOST,
                                        "Right Most":mvlib.PrimitiveFindLine.LINE_RIGHTMOST,
                                        "Left Strong":mvlib.PrimitiveFindLine.LINE_LEFTSTRONG,
                                        "Middle Strong":mvlib.PrimitiveFindLine.LINE_MIDDLESTRONG,
                                        "Right Strong":mvlib.PrimitiveFindLine.LINE_RIGHTSTRONG}),
                 RoiParam("roi", viewerTag="view")]
    
        def processScript(self, inputs, outputs, params, preInit):
            if "img" not in inputs:
                raise Exception("No input image")
    
            finder = mvlib.PrimitiveFindLine(polarity=params["Polarity"].get(),
                                min_contrast=params["Min Contrast"].get(),
                                min_shape=params["Min Shape"].get(),
                                find_mode=params["Find Mode"].get(),
                                rot_allowed=params["Rotation Allowed"].get(),
                                max_angle=params["Max Angle"].get())
            
            # Input ROI has priority
            rect = None
            if "search roi" in inputs:
                params["roi"].setEnabled(False)
                rect = inputs["search roi"]
                finder.set_roi(rect["x"], rect["y"], rect["width"], rect["height"])
            elif params["roi"].isEnabled():
                rect = params["roi"].getRect()
                finder.set_roi(rect["x"], rect["y"], rect["width"], rect["height"])
            else:
                finder.roi = None
    
            if "offset" in inputs:
                if "angle" in inputs["offset"]:
                    angle = inputs["offset"]["angle"]
                else:
                    angle = 0
                finder.set_offset(inputs["offset"]["x"],
                                  inputs["offset"]["y"],
                                  angle)
    
            outputs["result"] = finder.find_line(inputs["img"])
    
            RED = 0xff0000
            GREEN = 0xff00
            params["view"].updateImage(inputs["img"])        
            if outputs["result"].return_val != 0:
                if params["roi"].isEnabled():
                    params["roi"].setColor(RED)
                elif rect:
                    params["view"].AddRect(
                            rect["x"],
                            rect["y"],
                            rect["width"],
                            rect["height"], color=RED)
                    params["view"].DrawAddedObjects()
                outputs["found"] = 0
                outputs["score"] = 0
                outputs["center point"] = {
                    "x": 0,
                    "y": 0}
    
                raise Exception("Line Find Failed with return value: " + 
                      mvlib.utils.script_result_to_string(outputs["result"].return_val))
            else:
                if params["roi"].isEnabled():
                    params["roi"].setColor(GREEN)
                elif rect:
                    params["view"].AddRect(
                            rect["x"],
                            rect["y"],
                            rect["width"],
                            rect["height"], color=GREEN)
                params["view"].AddLine(outputs["result"].line_point_a_x,
                                       outputs["result"].line_point_a_y,
                                       outputs["result"].line_point_b_x,
                                       outputs["result"].line_point_b_y,
                                       3,
                                       0x00FF00)  # Green
                params["view"].DrawAddedObjects()
                outputs["found"] = outputs["result"].found
                outputs["score"] = outputs["result"].score
                outputs["center point"] = {
                    "x": outputs["result"].line_midpoint_x,
                    "y": outputs["result"].line_midpoint_y}
    
                log.info("Found: " + str(outputs["found"]))
                log.info("Score: " + str(outputs["score"]))
                log.info("Line Mid Point ({}, {})".format(
                    outputs["result"].line_midpoint_x,
                    outputs["result"].line_midpoint_y))       
    
    
    def __init__(self):
        super().__init__(Test_lineFinder.Test_lineFinder())

    def initialize(self):
        self.obj().name = "Test_lineFinder"
        for param in self.obj().params.values():
        
            if param.name == "Min Contrast":
                param.set(25)
            
            elif param.name == "Min Shape":
                param.set(30)
            
            elif param.name == "Max Angle":
                param.set(30)
            
            elif param.name == "Rotation Allowed":
                param.set(True)
            
            elif param.name == "Polarity":
                param.set(2)
            
            elif param.name == "Find Mode":
                param.set(3)
            
            elif param.name == "roi":
                param.set({
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32,
                    "angle": 0
                })
                param.setEnabled(False)
            
class outputAsString(ObjectManager):

    class outputAsString(Element):
    
        _name = "Simple output node for strings"
        _comment = "takes two strings, puts a delimiter in between them"
    
        def attributes(self):
    
            return [Input("str in"), Input("str in 2")], \
            [], \
            [StringParam("out str"), StringParam("delimiter")]
    
        def processScript(self, inputs, outputs, params, preInit):
            
            try:
                cLine = str(inputs["str in"])
            except KeyError:
                cLine = ""
    
            try: 
                tLine = str(inputs["str in 2"])
            except KeyError:
                tLine = ""
    
            delimiter = params["delimiter"].get()
            
            if cLine == "1":
                log.info("c is one!!")
            if cLine == "0":
                log.info("c is none :(")
            
            if tLine == "1":
                log.info("t is one!!")
            if tLine == "0":
                log.info("t is none :(")
            
            if cLine == "1" and tLine == "1":
                print("Negative")
            if cLine == "1" and tLine == "0":
                print("Positive")
            if cLine == "0" and tLine == "1":
                print("Invalid")
            if cLine == "0" and tLine == "0":
                print("Invalid")                                                                                                                                                                                                                                                                                                                                               
    
    
    def __init__(self):
        super().__init__(outputAsString.outputAsString())

    def initialize(self):
        self.obj().name = "outputAsString"
        for param in self.obj().params.values():
        
            if param.name == "out str":
                param.set('1  0')
            
            elif param.name == "delimiter":
                param.set('')
            

### global functions ###

g_gm = Graph()


### connections ###

def linksInit():

    global g_gm

    set_active_camera("9999999 U3V (JADAK - A Novanta Company-2978D00F9999999-9999999)")
    acquireImageCamera_e = acquireImageCamera().obj()
    g_gm.add_element(acquireImageCamera_e)
    
    featureFind_e = featureFind().obj()
    acquireImageCamera_e.outputs["img"].connect(featureFind_e.inputs["img"])
    g_gm.add_element(featureFind_e)
    
    RoiFromCenterPoint_e = RoiFromCenterPoint().obj()
    featureFind_e.outputs["center point"].connect(RoiFromCenterPoint_e.inputs["center point"])
    g_gm.add_element(RoiFromCenterPoint_e)
    
    Control_lineFinder_e = Control_lineFinder().obj()
    acquireImageCamera_e.outputs["img"].connect(Control_lineFinder_e.inputs["img"])
    RoiFromCenterPoint_e.outputs["roi"].connect(Control_lineFinder_e.inputs["search roi"])
    g_gm.add_element(Control_lineFinder_e)
    
    RoiFromCenterPoint1_e = RoiFromCenterPoint1().obj()
    featureFind_e.outputs["center point"].connect(RoiFromCenterPoint1_e.inputs["center point"])
    g_gm.add_element(RoiFromCenterPoint1_e)
    
    Test_lineFinder_e = Test_lineFinder().obj()
    acquireImageCamera_e.outputs["img"].connect(Test_lineFinder_e.inputs["img"])
    RoiFromCenterPoint1_e.outputs["roi"].connect(Test_lineFinder_e.inputs["search roi"])
    g_gm.add_element(Test_lineFinder_e)
    
    outputAsString_e = outputAsString().obj()
    Control_lineFinder_e.outputs["found"].connect(outputAsString_e.inputs["str in"])
    Test_lineFinder_e.outputs["found"].connect(outputAsString_e.inputs["str in 2"])
    g_gm.add_element(outputAsString_e)
    

### get results ###


    

### process function ###

def process():

    global g_gm
    return g_gm.execute()

### Context ###

class Context(ScriptContext):
    def __init__(self, args=[], kwargs=dict()):
        super().__init__(self, args=args, kwargs=kwargs, doc=__doc__)
        linksInit()
    def _on_enter(self):
        pass
    def _on_exit(self, exc_type, exc_val, exc_tb):
        global g_gm
        g_gm.postExecute()
    def _handle_message(self, msg):
        """
        msg contains 2 members:
            .label : source of the message (e.g."stdin")
            .msg   : The message string recieved from the source

        _handle mesage() returns True to abort the script, False otherwise
        """
        return super()._handle_message(msg)
    

### script ###

def main(*args, **kwargs):
    # Context() process params: "loop=...", "help", "?", "prtout[=0|1]" "profile[=...]"
    # All other params are stored in context,args and context.kwargs
    with Context(args=args, kwargs=kwargs) as context:
        if not context:
            # main() was called with "help" or "?"
            return
        count = 1
        while context.infinite or count <= context.loop:
            if HandleMessages():
                break
            try:
                state, output = process()
                if not state:
                    break
                #if context.prtout and output is not None:
                    #printResults(output)
                output = None
            except LoopTerminationException as e:
                break;
            except Exception as e:
                l(e)
                break;
            count += 1

if __name__ == "__main__":
    args = []
    kwargs = dict()
    for a in sys.argv[1:]:
        if "=" in a:
            v = a.split("=", maxsplit=1)
            kwargs[v[0]] = v[1]
        else:
            args.append(a)
    if not "prtout" in kwargs:
        kwargs["prtout"] = True

    main(*args, **kwargs)
    
########################################################################  
