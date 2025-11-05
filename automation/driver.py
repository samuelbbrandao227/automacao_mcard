from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def iniciar_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service()  # usa o chromedriver do PATH
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver