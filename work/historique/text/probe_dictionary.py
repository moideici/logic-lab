import urllib.request,re,json
u='https://kaikki.org/frwiktionary/Fran%C3%A7ais/meaning/c/ch/chat.html'
with urllib.request.urlopen(u,timeout=30)as r:s=r.read().decode();print(r.status)
print('\n'.join(re.findall(r'href=["\x27]([^"\x27]+json[^"\x27]*)',s)))
