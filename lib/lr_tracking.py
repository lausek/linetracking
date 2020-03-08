from .tracker import LineTracker

import cv2
import numpy as np

def clamp_bounds(n):
    return min(max(int(n), -6000), 6000)

class LRTracker(LineTracker):
    CHUNK_CNT = 5

    def __init__(self, cap):
        super().__init__(cap)

    def _color(self):
        from random import randint
        return (randint(0, 255), randint(0, 255), randint(0, 255))

    def _fit_line(self, roi, contour):
        [vx, vy, x0, y0] = cv2.fitLine(
            contour,
            #cv2.DIST_L2,
            cv2.DIST_L1,
            param=0,
            reps=0.01,
            aeps=0.01
        )

        if vy == 0:
            return

        m = vy / vx

        left, right = clamp_bounds(-x0 * m + y0), clamp_bounds(100 * m + y0)

        if self._preview:
            print(right, left)
            #cv2.circle(roi, (x0, y0), 4, (255, 0, 255))
            cv2.line(roi, (100, right), (0, left), self._color(), 2)

    def _process_chunk(self, chunk):
        # Convert to grayscale
        gray = cv2.cvtColor(chunk, cv2.COLOR_BGR2GRAY)

        # Gaussian blur
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # Color thresholding
        ret, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)

        contours, hierarchy = cv2.findContours(thresh.copy(), 1, cv2.CHAIN_APPROX_NONE)

        for contour in contours:
            self._fit_line(chunk, contour)

        if self._preview:
            pt1, pt2 = (0, 0), chunk.shape[:2]
            #cv2.rectangle(chunk, pt1, pt2, self._color())
            #cv2.drawContours(chunk, contours, -1, self._color(), 1)

        return None

    def _split_chunks(self, roi):
        #from pudb import set_trace; set_trace()

        height, width = roi.shape[:2]
        ch, cw = int(height / LRTracker.CHUNK_CNT), int(width / LRTracker.CHUNK_CNT)

        h = 0
        while h < height:

            w = 0
            while w < width:
                yield roi[h:h+ch, w:w+cw]
                w += cw

            h += ch

    def _process_frame(self, roi):
        for chunk in self._split_chunks(roi):
            a = self._process_chunk(chunk)

        if self._preview:
            cv2.imshow('Preview', roi)

        return None

        # Convert to grayscale
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Gaussian blur
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # Color thresholding
        ret, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)

        # Find the contours of the frame
        contours, hierarchy = cv2.findContours(thresh.copy(), 1, cv2.CHAIN_APPROX_NONE)

        if 0 < len(contours):
            print(hierarchy)

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

                if right < 0:
                    right = 0

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

            if cx <= 70:
                print("Turn Left")
            if 70 < cx < 100:
                print("On Track!")
            if 100 <= cx:
                print("Turn Right!")

            return cx

    def track_line(self):
        roi = self._get_frame()

        if roi is not None:
            return self._process_frame(roi)

        return None
