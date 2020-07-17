from selenium import webdriver


class Browser:
    def __init__(self, secret):
        self.options = webdriver.ChromeOptions()

        self.options.add_argument('user-data-dir={}'.format(secret['CHROME']['USER-DATA-DIR']))
        self.options.add_argument('profile-directory=Default')

        if secret['CHROME']['HEADLESS']:
            self.options.add_argument('disable-extensions')
            self.options.add_argument('disable-popup-blocking')
            self.options.add_argument('headless')
            self.options.add_argument('disable-gpu')
            self.options.add_argument('no-sandbox')
            self.options.add_argument('window-size=1920x1080')

        self.options.add_experimental_option('prefs', {
            'download.default_directory': secret['CHROME']['DOWNLOAD-DIR'],
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
        })

        self.driver = webdriver.Chrome(executable_path=secret['CHROME']['DRIVER'], options=self.options)

        if secret['CHROME']['HEADLESS']:
            self.driver.command_executor._commands['send_command'] \
                = ('POST', '/session/$sessionId/chromium/send_command')
            self.driver.execute('send_command', {
                'cmd': 'Page.setDownloadBehavior',
                'params': {
                    'behavior': 'allow',
                    'downloadPath': secret['CHROME']['DOWNLOAD-DIR']
                }
            })

    def terminate(self):
        self.driver.close()
        self.driver.quit()
