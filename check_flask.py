# -*- coding: utf-8 -*-
import urllib.request

resp = urllib.request.urlopen('http://localhost:5000/dashboard')
html = resp.read().decode('utf-8', errors='replace')

funcs = ['renderClientTab','renderClassification','getClassificationBadge',
         'Alertas Proativos','renderAdminTab','renderPerformanceTab']
for fn in funcs:
    found = fn in html
    line = html[:html.find(fn)].count('\n')+1 if found else -1
    status = 'OK' if found else 'MISSING'
    print(f'{status} {fn} (linha ~{line})')

print(f'\nTotal HTML chars: {len(html)}')
