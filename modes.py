from enum import Enum


class VideoModes(Enum):
    WEBCAM = 1
    VIDEO = 2
    IMAGES = 3

# Mapping from enum to string
VIDEOMODES_STR_MAP = {
    VideoModes.WEBCAM: 'Webcam',
    VideoModes.VIDEO: 'Video File',
    VideoModes.IMAGES: 'Image Sequence',
}