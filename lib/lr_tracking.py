from .tracker import LineTracker

import cv2
import numpy as np

class LRTracker(LineTracker):
    def __init__(self, cap):
        super().__init__(cap)

    def track_line(self):
        roi = self._get_frame()
        if roi is None:
            return None

        # Convert to grayscale
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Gaussian blur
        blur = cv2.GaussianBlur(gray,(5,5),0)

        # Color thresholding
        ret, thresh = cv2.threshold(blur,60,255,cv2.THRESH_BINARY_INV)

        # Find the contours of the frame
        contours, hierarchy = cv2.findContours(thresh.copy(), 1, cv2.CHAIN_APPROX_NONE)

        if 0 < len(contours):

            #cv2.line(roi, (10, 50), (100, 200), (255, 255, 0), 2)

            for contour in contours:
                [vx, vy, x0, y0] = cv2.fitLine(
                    contour,
                    #cv2.DIST_L2,
                    cv2.DIST_L1,
                    param=0,
                    reps=0.01,
                    aeps=0.01
                )

                if vy == 0:
                    continue

                m = vy / vx

                left, right = int(-x0 * m + y0), int(100 * m + y0)
                print(m)
                print(left, right)

                if self._preview:
                    cv2.circle(roi, (x0, y0), 4, (255, 0, 255))
                    cv2.line(roi, (100, right), (0, left), (255, 0, 0), 2)

            #c = max(contours, key=cv2.contourArea)
            #M = cv2.moments(c)

            #if M['m00'] == 0:
            #    return None

            #cx = int(M['m10']/M['m00'])
            #cy = int(M['m01']/M['m00'])

            cx, cy = 0, 0

            if self._preview:
                cv2.drawContours(roi, contours, -1, (0, 255, 0), 1)

                cv2.imshow('Preview', roi)

            if cx >= 100:
                print("Turn Right!")
            if cx < 100 and cx > 70:
                print("On Track!")
            if cx <= 70:
                print("Turn Left")

            return cx
        return -1
