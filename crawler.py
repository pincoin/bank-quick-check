import datetime
import json
import os
import re
from io import BytesIO

import requests
from PIL import Image
from bs4 import BeautifulSoup as bs

import chrome
import helpers

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


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
    quics_img_element = driver.find_element_by_css_selector('img[src*="quics"]')

    # 2-5. 키맵 난수 해시값 구하기 eb51535f24ac - keypad_useyn의 뒤에 붙는 값과 일치
    keymap = quics_img_element.get_attribute('usemap').replace('#divKeypad', '')[:-3]

    # 2-6. 가상 키패드 이미지는 총 14개 영역(area)
    area_elements = driver.find_elements_by_css_selector('map > area')

    area_hash_list = []

    # 2-7. 자바스크립트 메소드에서 hide, cls, del 외에 put(해시문자열) 10개 구하기
    area_pattern = re.compile(r"'(\w+)'")

    for area in area_elements:
        re_matched = area_pattern.findall(area.get_attribute('onmousedown'))
        if re_matched:
            area_hash_list.append(re_matched[0])

    # 2-8. 가상 키패드 이미지 실제로 다운로드
    driver.get(quics_img_element.get_attribute('src'))

    # 2-9. 셀레늄 크롬 브라우저는 이미지 다운로드 해도 HTML 문서 형태로 불러옴
    keypad_img_element = driver.find_element_by_tag_name('img')

    # 2-10. 브라우저 크기 스크린샷에서 가상키보드 이미지 잘라내기
    screenshot = Image.open(BytesIO(driver.get_screenshot_as_png()))
    keypad = screenshot.crop(box=(
        keypad_img_element.location['x'],
        keypad_img_element.location['y'],
        keypad_img_element.location['x'] + keypad_img_element.size['width'],
        keypad_img_element.location['y'] + keypad_img_element.size['height'],
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
    box_5th = Image.open(os.path.join(BASE_DIR, 'assets', 'kbstar', '5.png'))
    box_7th = Image.open(os.path.join(BASE_DIR, 'assets', 'kbstar', '7.png'))
    box_8th = Image.open(os.path.join(BASE_DIR, 'assets', 'kbstar', '8.png'))
    box_9th = Image.open(os.path.join(BASE_DIR, 'assets', 'kbstar', '9.png'))
    box_0th = Image.open(os.path.join(BASE_DIR, 'assets', 'kbstar', '0.png'))

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
                diff = helpers.rmsdiff(crop, box)
                if diff < 13:
                    keypad_num_list += [key]
            except Exception as e:
                print(e)

    # 키패드 실제 순서
    print(keypad_num_list)

    keypad_dict = {}
    # 고정값
    keypad_dict['1'] = area_hash_list[0]
    keypad_dict['2'] = area_hash_list[1]
    keypad_dict['3'] = area_hash_list[2]
    keypad_dict['4'] = area_hash_list[3]
    keypad_dict['6'] = area_hash_list[5]

    # 변동값
    for idx, num in enumerate(keypad_num_list):
        if idx == 0:
            keypad_dict[str(num)] = area_hash_list[4]
        elif idx == 1:
            keypad_dict[str(num)] = area_hash_list[6]
        elif idx == 2:
            keypad_dict[str(num)] = area_hash_list[7]
        elif idx == 3:
            keypad_dict[str(num)] = area_hash_list[8]
        elif idx == 4:
            keypad_dict[str(num)] = area_hash_list[9]

    for k, v in keypad_dict.items():
        print(k, v)

    hashed_password = ''
    for p in secret['BANK']['KB']['PASSWORD']:
        hashed_password += keypad_dict[p]

    print(hashed_password)

    # 5. 헤더와 폼 데이터를 구성하여 requests 객체로 post 메소드 전송한다.

    today = datetime.datetime.today()
    this_year = today.strftime('%Y')
    this_month = today.strftime('%m')
    this_day = today.strftime('%d')
    this_all = today.strftime('%Y%m%d')

    month_before = today - datetime.timedelta(days=1)

    month_before_year = month_before.strftime('%Y')
    month_before_month = month_before.strftime('%m')
    month_before_day = month_before.strftime('%d')
    month_before_all = month_before.strftime('%Y%m%d')

    cookies = {
        '_KB_N_TIKER': 'N',
        'JSESSIONID': jsessionid,
        'QSID': qsid,
        'delfino.recentModule': 'G3',
    }

    headers = {
        'Pragma': 'no-cache',
        'Origin': 'https://obank.kbstar.com',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.6,en;q=0.4,la;q=0.2,da;q=0.2',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/61.0.3163.79 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded;  charset=UTF-8',
        'Accept': 'text/html, */*; q=0.01',
        'Cache-Control': 'no-cache',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'Referer': 'https://obank.kbstar.com/quics?page=C025255&cc=b028364:b028702&QSL=F',
        'DNT': '1',
    }

    params = (
        ('chgCompId', 'b028770'),
        ('baseCompId', 'b028702'),
        ('page', 'C025255'),
        ('cc', 'b028702:b028770'),
    )

    data = [
        # http://koreanstudies.com/unicode-converter.html
        ('KEYPAD_TYPE_{}'.format(keymap), '3'),
        ('KEYPAD_HASH_{}'.format(keymap), hashed_password),
        ('KEYPAD_USEYN_{}'.format(keymap), keypad_useyn),
        ('KEYPAD_INPUT_{}'.format(keymap), '\uBE44\uBC00\uBC88\uD638'),  # '비밀번호'
        ('signed_msg', ''),
        ('\uC694\uCCAD\uD0A4', ''),  # 요청키
        ('\uACC4\uC88C\uBC88\uD638', secret['BANK']['KB']['ACCOUNT']),  # '계좌번호' (숫자만)
        ('\uC870\uD68C\uC2DC\uC791\uC77C\uC790', month_before_all),  # '조회시작일자' (20201123)
        ('\uC870\uD68C\uC885\uB8CC\uC77C', this_all),  # '조회종료일' (20201123)
        ('\uACE0\uAC1D\uC2DD\uBCC4\uBC88\uD638', secret['BANK']['KB']['ID']),  # '고객식별번호' (인터넷뱅킹 ID) 개인은 빈문자열
        ('\uBE60\uB978\uC870\uD68C', 'Y'),  # '빠른조회'
        ('\uC870\uD68C\uACC4\uC88C', secret['BANK']['KB']['ACCOUNT']),  # '조회계좌'
        ('\uBE44\uBC00\uBC88\uD638', secret['BANK']['KB']['PASSWORD']),  # '비밀번호'
        ('USEYN_CHECK_NAME_{}'.format(keymap), 'Y'),
        ('\uAC80\uC0C9\uAD6C\uBD84', '2'),  # '검색구분'
        # ('\uC8FC\uBBFC\uC0AC\uC5C5\uC790\uBC88\uD638', birthday), # '주민사업자번호' (개인/개인사업자)
        ('\uace0\uac1d\u0049\u0044', secret['BANK']['KB']['ID']),  # '고객ID' (법인 인터넷뱅킹 ID)
        ('\uC870\uD68C\uC2DC\uC791\uB144', month_before_year),  # '조회시작년' (2020)
        ('\uC870\uD68C\uC2DC\uC791\uC6D4', month_before_month),  # '조회시작월' (11)
        ('\uC870\uD68C\uC2DC\uC791\uC77C', month_before_day),  # '조회시작일' (23)
        ('\uC870\uD68C\uB05D\uB144', this_year),  # '조회끝년' (2020)
        ('\uC870\uD68C\uB05D\uC6D4', this_month),  # '조회끝월' (11)
        ('\uC870\uD68C\uB05D\uC77C', this_day),  # '조회끝일' (23)
        ('\uC870\uD68C\uAD6C\uBD84', '2'),  # '조회구분'
        ('\uC751\uB2F5\uBC29\uBC95', '2'),  # '응답방법'
    ]

    print(headers)
    print(params)
    print(cookies)
    print(data)

    r = requests.post('https://obank.kbstar.com/quics', headers=headers, params=params, cookies=cookies, data=data)

    # 6. HTML 응답 결과를 알맞게 파싱
    soup = bs(r.text, 'html.parser')

    transactions = soup.select('#pop_contents > table.tType01 > tbody > tr')

    transaction_list = []

    print(transactions)


if __name__ == '__main__':
    main()
