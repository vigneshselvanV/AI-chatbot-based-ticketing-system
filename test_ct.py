import urllib.request
import re
import sys

def test_ct():
    req = urllib.request.Request(
        'https://www.confirmtkt.com/trains-between-stations/MAS/CSTM', 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    res = urllib.request.urlopen(req)
    html = res.read().decode('utf-8')
    
    # Let's save html
    with open("debug_ct.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    print("Done. Saved debug_ct.html")

if __name__ == "__main__":
    test_ct()
