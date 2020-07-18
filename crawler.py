import json
import math
import operator
import os
import re
import time
from functools import reduce
from io import BytesIO

from PIL import (
    Image, ImageChops
)

import chrome

CURRENT_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))


def rmsdiff(im1, im2):
    h = ImageChops.difference(im1, im2).histogram()
    return math.sqrt(reduce(operator.add,
                            map(lambda h, i: h * (i ** 2), h, range(256))
                            ) / (float(im1.size[0]) * im1.size[1]))


def main():
    secret = json.loads(open('secret.json').read())

    # 1. 셀레늄 크롬 브라우저 열기
    browser = chrome.Browser(secret)
    driver = browser.driver
    driver.implicitly_wait(3)

    driver.get('https://obank.kbstar.com/quics?page=C025255&cc=b028364:b028702&QSL=F#loading')

    # 2. 헤더 구성을 위한 세션, 쿠키 등 각종 데이터 읽기
    # 2-1. JSESSIONID 쿠키 (예: GwyGfTkKjNgTLGNFLLGW9QhCmyCKV1y0nYswvJmTXYpzmQQTXGnX!-634445011)
    jsessionid = ''

    if driver.get_cookie('JSESSIONID'):
        jsessionid = driver.get_cookie('JSESSIONID').get('value')

    # 2-2. QSID 쿠키 (예: 6209&&GwyGfTkKjNgTLGNFLLGW9QhCmyCKV1y0nYswvJmTXYpzmQQTXGnX!-634445011!1595090154373)
    qsid = ''

    if driver.get_cookie('QSID'):
        qsid = driver.get_cookie('QSID').get('value')

    # 2-3. 마우스입력 사용 유무 (예: USEYN_CHECK_NAME_eb51535f24ac) 뒤에 난수 해시값이 있음
    keypad_useyn = driver.find_element_by_css_selector('input[id*="KEYPAD_USEYN"]').get_attribute('value')

    # 2-4. 가상 키패드 이미지 객체 구하기
    quics_img = driver.find_element_by_css_selector('img[src*="quics"]')

    # 2-5. 키맵 난수 해시값 구하기 eb51535f24ac - keypad_useyn의 뒤에 붙는 값과 일치
    keymap = quics_img.get_attribute('usemap').replace('#divKeypad', '')[:-3]

    # 2-6. 가상 키패드 이미지는 총 14개 영역(area)
    area_list = driver.find_elements_by_css_selector('map > area')

    area_hash_list = []

    # 2-7. 자바스크립트 메소드에서 hide, cls, del 외에 put(해시문자열) 10개 구하기
    area_pattern = re.compile(r"'(\w+)'")

    for area in area_list:
        re_matched = area_pattern.findall(area.get_attribute('onmousedown'))
        if re_matched:
            area_hash_list.append(re_matched[0])

    # 2-8. 가상 키패드 이미지 실제로 다운로드
    driver.get(quics_img.get_attribute('src'))

    # 2-9. 셀레늄 크롬 브라우저 통해 이미지 열기 시뮬레이션 하므로 다시 img 태그 가져오기
    img_tag = driver.find_element_by_tag_name('img')

    # 2-10. 전체 스크린샷에서 가상키보드 이미지 잘라내기
    screenshot = Image.open(BytesIO(driver.get_screenshot_as_png()))
    keypad = screenshot.crop(box=(
        img_tag.location['x'],
        img_tag.location['y'],
        img_tag.location['x'] + img_tag.size['width'],
        img_tag.location['y'] + img_tag.size['height'],
    ))
    # keypad.save('keypad.png')

    print(jsessionid)
    print(qsid)
    print(keypad_useyn)
    print(keymap)

    for i in area_hash_list:
        print(i, len(i))

    # 3. 셀레늄 크롬 브라우저 종료
    browser.terminate()

    # 4. 키패드 이미지 매칭으로 비밀번호 해시 구하기

    # 57x57 박스 이미지
    box_5th = Image.open(os.path.join(CURRENT_PACKAGE_DIR, 'assets', 'kbstar', '5.png'))
    box_7th = Image.open(os.path.join(CURRENT_PACKAGE_DIR, 'assets', 'kbstar', '7.png'))
    box_8th = Image.open(os.path.join(CURRENT_PACKAGE_DIR, 'assets', 'kbstar', '8.png'))
    box_9th = Image.open(os.path.join(CURRENT_PACKAGE_DIR, 'assets', 'kbstar', '9.png'))
    box_0th = Image.open(os.path.join(CURRENT_PACKAGE_DIR, 'assets', 'kbstar', '0.png'))

    box_dict = {
        5: box_5th,
        7: box_7th,
        8: box_8th,
        9: box_9th,
        0: box_0th,
    }

    # 57x57 가상 키패드 잘라낸 이미지 (실제 영역 56x56)
    # 위치에 따른 실제 숫자 찾기
    crop_5th = keypad.crop(box=(74, 99, 131, 156))  # 75,100,130,155
    crop_7th = keypad.crop(box=(16, 157, 73, 214))  # 17,158,72,213
    crop_8th = keypad.crop(box=(74, 157, 131, 214))  # 75,158,130,213
    crop_9th = keypad.crop(box=(132, 157, 189, 214))  # 133,158,188,213
    crop_0th = keypad.crop(box=(74, 215, 131, 272))  # 75,216,130,271

    crop_list = [crop_5th, crop_7th, crop_8th, crop_9th, crop_0th]

    keypad_num_list = []

    for idx, crop in enumerate(crop_list):
        for key, box in box_dict.items():
            try:
                diff = rmsdiff(crop, box)
                if diff < 13:
                    keypad_num_list += [key]
            except Exception as e:
                print(e)

    # 키패드 실제 순서
    print(keypad_num_list)

    PW_DIGITS = {}
    # 고정값
    PW_DIGITS['1'] = area_hash_list[0]
    PW_DIGITS['2'] = area_hash_list[1]
    PW_DIGITS['3'] = area_hash_list[2]
    PW_DIGITS['4'] = area_hash_list[3]
    PW_DIGITS['6'] = area_hash_list[5]

    # 변동값
    for idx, num in enumerate(keypad_num_list):
        if idx == 0:
            PW_DIGITS[str(num)] = area_hash_list[4]
        elif idx == 1:
            PW_DIGITS[str(num)] = area_hash_list[6]
        elif idx == 2:
            PW_DIGITS[str(num)] = area_hash_list[7]
        elif idx == 3:
            PW_DIGITS[str(num)] = area_hash_list[8]
        elif idx == 4:
            PW_DIGITS[str(num)] = area_hash_list[9]

    for k, v in PW_DIGITS.items():
        print(k, v)

    hashed_password = ''
    for p in secret['BANK']['KB']['PASSWORD']:
        hashed_password += PW_DIGITS[p]

    print(hashed_password)

    # 5. Send post method 헤더와 폼 데이터를 구성하여 requests 객체로 post 메소드 전송한다.

    # 6. Parses HTML response appropriately

    time.sleep(0)


if __name__ == '__main__':
    main()
