from .tracker import LineTracker

import cv2
import math
import numpy as np

def clamp_bounds(n):
    return min(max(int(n), -6000), 6000)

class LRTracker(LineTracker):
    CHUNK_CNT = 5
    CHUNK_SIZE = 50
    SLOPE_DELTA = 10

    _guiding_chunks = []

    def __init__(self, cap):
        super().__init__(cap)

    def _draw_rect(self, roi, rect, color):
        pt1, pt2 = (rect[0], rect[1]), (rect[0] + LRTracker.CHUNK_SIZE, rect[1] + LRTracker.CHUNK_SIZE)
        cv2.rectangle(roi, pt1, pt2, color)

    def _slice(self, roi, rect):
        return roi[rect[1]:rect[1] + LRTracker.CHUNK_SIZE, rect[0]:rect[0] + LRTracker.CHUNK_SIZE]

    def _slope_is_odd(self, m, mr):
        angle = math.atan((m - mr) / 1 + (m * mr))
        angle = math.degrees(angle)
        return not (0 < angle < 20)

    def _slider(self, roi, main):
        def relative(base, rel):
            return (base[0]+rel[0], base[1]+rel[1], base[2]+rel[2], base[3]+rel[3])

        orange, purple = (255, 127, 0), (128, 0, 128)
        size, slope_delta = LRTracker.CHUNK_SIZE, LRTracker.SLOPE_DELTA

        # calculate rectangles of sibling chunks
        sib_left = relative(main, (-size, 0, 0, 0))
        sib_right = relative(main, (+size, 0, 0, 0))

        # determine slopes in each chunk
        sm = self._slopes_in_chunk(self._slice(roi, main))
        sl = self._slopes_in_chunk(self._slice(roi, sib_left))
        sr = self._slopes_in_chunk(self._slice(roi, sib_right))

        # determine difference between main slope and sibling slope
        sm = sm[0] if sm else None
        sl = sl[0] if sl else None
        sr = sr[0] if sr else None
        sld, srd = None, None

        # TODO: error? there should always be a slope in the main chunk (?)
        if sm is None:
            return

        # if slope in left/right sibling is abnormal, repeat this algorithm for the sibling

        if not sl is None:
            if self._slope_is_odd(sm, sl):
                print('kreuzung links')
                self._slider(roi, relative(sib_left, (0, -size, 0, 0)))

        if not sr is None:
            if self._slope_is_odd(sm, sr):
                print('kreuzung rechts')
                self._slider(roi, relative(sib_right, (0, -size, 0, 0)))

        print(sld, srd)
        if (sld and sld < slope_delta) or (srd and srd < slope_delta):
            print('keine kreuzungen')

        if self._preview:
            self._draw_rect(roi, main, orange)
            self._draw_rect(roi, sib_left, purple)
            self._draw_rect(roi, sib_right, purple)

    def _color(self):
        from random import randint
        return (randint(0, 255), randint(0, 255), randint(0, 255))

    def _slope(self, roi, contour):
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

        if self._preview:
            left, right = clamp_bounds(-x0 * m + y0), clamp_bounds(100 * m + y0)
            #print(right, left)
            #cv2.circle(roi, (x0, y0), 4, (255, 0, 255))
            cv2.line(roi, (100, right), (0, left), self._color(), 2)

        return m

    def _slopes_in_chunk(self, chunk):
        if chunk.size == 0:
            return

        # Convert to grayscale
        gray = cv2.cvtColor(chunk, cv2.COLOR_BGR2GRAY)

        # Gaussian blur
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # Color thresholding
        ret, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)

        contours, hierarchy = cv2.findContours(thresh.copy(), 1, cv2.CHAIN_APPROX_NONE)

        slopes = [self._slope(chunk, contour) for contour in contours]

        if self._preview:
            pt1, pt2 = (0, 0), chunk.shape[:2]
            #cv2.rectangle(chunk, pt1, pt2, self._color())
            #cv2.drawContours(chunk, contours, -1, self._color(), 1)

        return slopes

    #def _split_chunks(self, roi):
    #    #from pudb import set_trace; set_trace()

    #    height, width = roi.shape[:2]
    #    ch, cw = int(height / LRTracker.CHUNK_CNT), int(width / LRTracker.CHUNK_CNT)

    #    h = 0
    #    while h < height:

    #        w = 0
    #        while w < width:
    #            yield roi[h:h+ch, w:w+cw]
    #            w += cw

    #        h += ch

    def _process_frame(self, roi):
        size = LRTracker.CHUNK_SIZE
        mid = int(roi.shape[1] / 2)
        main = (
            int(mid - size / 2),
            roi.shape[0] - size,
            size,
            size
        )

        self._slider(roi, main)

        #for chunk in self._split_chunks(roi):
        #    a = self._process_chunk(chunk)

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
            #print(hierarchy)

            #cv2.line(roi, (10, 50), (100, 200), (255, 255, 0), 2)

            #for contour in contours:
            #    [vx, vy, x0, y0] = cv2.fitLine(
            #        contour,
            #        #cv2.DIST_L2,
            #        cv2.DIST_L1,
            #        param=0,
            #        reps=0.01,
            #        aeps=0.01
            #    )

            #    if vy == 0:
            #        continue

            #    m = vy / vx

            #    left, right = int(-x0 * m + y0), int(100 * m + y0)

            #    if right < 0:
            #        right = 0

            #    if self._preview:
            #        cv2.circle(roi, (x0, y0), 4, (255, 0, 255))
            #        cv2.line(roi, (100, right), (0, left), (255, 0, 0), 2)

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
