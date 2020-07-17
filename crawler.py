import json
import time

import chrome


def main():
    secret = json.loads(open('secret.json').read())

    # 1. Selenium 브라우저를 띄운다.
    browser = chrome.Browser(secret)
    driver = browser.driver
    driver.implicitly_wait(3)

    driver.get(secret['BANK']['KB']['URL'])

    # 2. 생성된 세션값, 쿠키값 등 헤더 구성을 위한 데이터를 읽는다.
    jsessionid = ''
    qsid = ''

    if driver.get_cookie('JSESSIONID'):
        jsessionid = driver.get_cookie('JSESSIONID').get('value')

    if driver.get_cookie('QSID'):
        qsid = driver.get_cookie('QSID').get('value')

    keyapd_useyn = driver.find_element_by_css_selector('input[id*="KEYPAD_USEYN"]').get_attribute('value')
    quics_img = driver.find_element_by_css_selector('img[src*="quics"]')
    area_list = driver.find_elements_by_css_selector('map > area')

    print(jsessionid)
    print(qsid)
    print(keyapd_useyn)
    print(quics_img)
    print(area_list)

    # 3. 가상키보드 이미지 매칭으로 비밀번호를 해싱한다.

    # 4. 헤더와 폼 데이터를 구성하여 requests 객체로 post 메소드 전송한다.

    # 5. HTML 결과를 알맞게 파싱한다.

    time.sleep(3)

    browser.terminate()


if __name__ == '__main__':
    main()
