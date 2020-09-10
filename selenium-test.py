#!/usr/bin/env python

# Copyright 2015 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import json
import time
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--userindex', type=int,
                    help='the index of the user for which the sequence is run')
args = parser.parse_args()

with open('users.json') as json_file:
    data = json.load(json_file)

user_email = data[args.userindex]['email']

user_xpath = '//*[@id="input-16"]'
pwd_xpath = '//*[@id="input-19"]'

def start_app():
  driver = webdriver.Remote(
    command_executor='http://selenium-hub:4444/wd/hub',
    desired_capabilities=getattr(DesiredCapabilities, "FIREFOX")
  )
  driver.get("https://az.nuvolos.cloud/org/29/space/585/instance/3433/snapshot/26689/application/37133")

  element = WebDriverWait(driver, 300).until(EC.element_to_be_clickable((By.XPATH, user_xpath)))
  element.click()
  element.send_keys(user_email)
  element = WebDriverWait(driver, 300).until(EC.element_to_be_clickable((By.XPATH, pwd_xpath)))
  element.click()
  element.send_keys('12345678Aa.')
  element = WebDriverWait(driver, 300).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".v-btn--contained.secondary > .v-btn__content")))
  element.click()
  driver.get_screenshot_as_file('/tmp/app_started.png')
  time.sleep(600)
  driver.quit()

start_app()
#check_browser("FIREFOX")
#check_browser("CHROME")

