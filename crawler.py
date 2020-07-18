import json
import math
import operator
import re
import time
from functools import reduce
from io import BytesIO

from PIL import (
    Image, ImageChops
)

import chrome


def rmsdiff(im1, im2):
    h = ImageChops.difference(im1, im2).histogram()
    return math.sqrt(reduce(operator.add,
                            map(lambda h, i: h * (i ** 2), h, range(256))
                            ) / (float(im1.size[0]) * im1.size[1]))


def main():
    secret = json.loads(open('secret.json').read())

    # 1. Selenium 브라우저를 띄운다.
    browser = chrome.Browser(secret)
    driver = browser.driver
    driver.implicitly_wait(3)

    driver.get('https://obank.kbstar.com/quics?page=C025255&cc=b028364:b028702&QSL=F#loading')

    # 2. 생성된 세션값, 쿠키값 등 헤더 구성을 위한 데이터를 읽는다.
    jsessionid = ''

    if driver.get_cookie('JSESSIONID'):
        jsessionid = driver.get_cookie('JSESSIONID').get('value')

    qsid = ''

    if driver.get_cookie('QSID'):
        qsid = driver.get_cookie('QSID').get('value')

    # 마우스로 입력 유무
    keyapd_useyn = driver.find_element_by_css_selector('input[id*="KEYPAD_USEYN"]').get_attribute('value')

    # 가상 키보드 이미지
    quics_img = driver.find_element_by_css_selector('img[src*="quics"]')

    # 가상 키보드 이미지 매핑 영역(area)
    area_list = driver.find_elements_by_css_selector('map > area')

    area_hash_list = []

    # TODO 왜 패턴 매칭하지?
    area_pattern = re.compile("'(\w+)'")

    for area in area_list:
        re_matched = area_pattern.findall(area.get_attribute('onmousedown'))
        if re_matched:
            area_hash_list.append(re_matched[0])

    keymap = quics_img.get_attribute('usemap').replace('#divKeypad', '')[:-3]

    # 가상 키보드 이미지 다운로드
    driver.get(quics_img.get_attribute('src'))

    img_tag = driver.find_element_by_tag_name('img')

    # 화면 캡처에서 가상키보드 이미지 잘라내기
    screenshot = Image.open(BytesIO(driver.get_screenshot_as_png()))
    keypad = screenshot.crop(box=(
        img_tag.location['x'],
        img_tag.location['y'],
        img_tag.location['x'] + img_tag.size['width'],
        img_tag.location['y'] + img_tag.size['height'],
    ))
    keypad.save('keyboard.png')

    # 3. Selenium 브라우저 종료한다.
    browser.terminate()

    # 4. 가상키보드 이미지 매칭으로 비밀번호를 해싱한다.

    # 5. 헤더와 폼 데이터를 구성하여 requests 객체로 post 메소드 전송한다.

    # 6. HTML 결과를 알맞게 파싱한다.

    time.sleep(1)


if __name__ == '__main__':
    main()
