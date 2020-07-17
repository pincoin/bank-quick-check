import json
import time

from selenium import webdriver


def main():
    secret = json.loads(open('secret.json').read())

    options = webdriver.ChromeOptions()
    options.add_argument('user-data-dir={}'.format(secret['CHROME']['USER-DATA-DIR']))
    options.add_argument('profile-directory=Default')

    if secret['CHROME']['HEADLESS']:
        options.add_argument('disable-extensions')
        options.add_argument('disable-popup-blocking')
        options.add_argument('headless')
        options.add_argument('disable-gpu')
        options.add_argument('no-sandbox')
        options.add_argument('window-size=1920x1080')

    options.add_experimental_option('prefs', {
        'download.default_directory': secret['CHROME']['DOWNLOAD-DIR'],
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
    })

    driver = webdriver.Chrome(executable_path=secret['CHROME']['DRIVER'], options=options)

    if secret['CHROME']['HEADLESS']:
        driver.command_executor._commands['send_command'] \
            = ('POST', '/session/$sessionId/chromium/send_command')
        driver.execute('send_command', {
            'cmd': 'Page.setDownloadBehavior',
            'params': {
                'behavior': 'allow',
                'downloadPath': secret['CHROME']['DOWNLOAD-DIR']
            }
        })

    driver.implicitly_wait(3)

    driver.get(secret['BANK']['KB']['URL'])

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

    time.sleep(3)

    driver.close()

    driver.quit()


if __name__ == '__main__':
    main()
