import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen
import tarfile
from io import BytesIO
import re
import subprocess
import os

def getVersion(url_text):
    m = re.search('OpenSSL (.+?) release', url_text)
    if m:
        found = m.group(1)
        return found

ARCH = '-x64'
url = 'https://git.openssl.org'
url_tags = 'https://git.openssl.org/?p=openssl.git;a=tags'
reqs = requests.get(url_tags)
soup = BeautifulSoup(reqs.text, 'html.parser')
urls = soup.find_all('a')

f = open("Download-log.txt", "w")
# Grab all commit hashes for tagged releases
for i in range(len(urls)):
    url_href = urls[i].get('href')
    url_text = urls[i].text
    # Filter releases that are not FIPS
    openssl_release = 'a=tag' in url_href and 'release tag' in url_text and 'FIPS' not in url_text
    if openssl_release:
        try:
            commit = url_href.split("h=",1)[1]
            snapshot = f'https://git.openssl.org/?p=openssl.git;a=snapshot;h={commit};sf=tgz'
            directory_name = 'openssl-' +commit[0:7]
            #  Download and extract
            r = urlopen(snapshot)
            t = tarfile.open(name=None, fileobj=BytesIO(r.read()))
            t.extractall(getVersion(url_text) + ARCH)
            t.close()
            
            # Build and extract static built openssl binary
            build_directory = os.path.dirname(os.path.realpath(__file__)) + '/'  + getVersion(url_text) + ARCH +'/'
            full_path = build_directory + '/' + directory_name + '/'
            subprocess.run([full_path + 'Configure', 'no-shared',  'CFLAGS=-g', 
                            f'--prefix={build_directory}', f'--openssldir={build_directory}'], cwd=full_path)
            subprocess.run(['make'], cwd=full_path, shell=True)
            subprocess.run(['cp', full_path + 'apps/openssl', build_directory ] )

            # Remove directory
            subprocess.run(["rm", "-R", full_path])
            f.write(url_text + ' - PASSED')
        except:
            f.write(url_text + ' - FAILED')
f.close()



    
