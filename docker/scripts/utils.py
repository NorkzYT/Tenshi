#!/usr/bin/env python3
"""
Tenshi utilities: screenshot capture, template matching, and wait routines.
"""
import logging
import os
import time

import cv2
import numpy as np
from PIL import ImageGrab

logger = logging.getLogger(__name__)
DEBUG_OPENCV = os.environ.get("DEBUG_OPENCV", "0") == "1"
FASTAPI_BASE = "http://127.0.0.1:8000"
CDP_ENDPOINT = "http://127.0.0.1:9222"
RELOAD_TPL = "/tenshi/images/reload-button-template.png"
