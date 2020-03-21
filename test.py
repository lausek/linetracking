import cv2
import sys
import time

class Camera(object):
    def __init__(self, path=None):
        self._source = 0 if path is None else path
        self._cap = cv2.VideoCapture(self._source)

    def resolution(self):
        width = self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        return (int(width), int(height))

    def read(self):
        ret, frame = self._cap.read()
        return frame

def main():
    try:
        idx = sys.argv.index('--in')
        path = sys.argv[idx + 1]
    except ValueError:
        path = None

    cam = Camera(path)

    if '--lr' in sys.argv:
        from lib import LRTracker
        ln = LRTracker(cam)
    else:
        from lib import ContourTracker
        ln = ContourTracker(cam)

    if '--preview' in sys.argv:
        ln.preview(True)

    autoplay = '--manual' not in sys.argv
    
    while True:
        print(ln.track_line())

        if autoplay:
            cv2.waitKey(1)
            time.sleep(0.1)
        else:
            cv2.waitKey(0)
    
    cv2.closeAllWindows()

if __name__ == '__main__':
    main()
