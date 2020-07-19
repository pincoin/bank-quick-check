import math
import operator
from functools import reduce

from PIL import ImageChops


def rmsdiff(im1, im2):
    # 제곱평제곱근(root mean square)을 이용한 이미지 비교 함수
    # 차이가 0이면 완전 일치, n 오차까지는 동일한 것으로 간주
    h = ImageChops.difference(im1, im2).histogram()
    return math.sqrt(reduce(operator.add,
                            map(lambda h, i: h * (i ** 2), h, range(256))
                            ) / (float(im1.size[0]) * im1.size[1]))
