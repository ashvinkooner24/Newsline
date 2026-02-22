import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)
driver.get("https://www.imnda.ie/about-mnd")

# Find all <script> tags
scripts = driver.find_elements("tag name", "script")

links = []
for s in scripts:
    js = s.get_attribute("innerHTML")
    matches = re.findall(r'location\.href\s*=\s*"([^"]+)"', js)
    links.extend(matches)

print(links)  

driver.quit()