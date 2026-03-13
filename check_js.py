# -*- coding: utf-8 -*-
import re

with open(r'C:\Users\lenov\MFL_Digital_Solutions\frontend\dashboards\dashboard_completo_html.html', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Extrai o JS do script tag
m = re.search(r'<script>(.*?)</script>', content, re.DOTALL)
if not m:
    print('Nenhuma tag script encontrada')
else:
    js = m.group(1)
    opens = js.count('{')
    closes = js.count('}')
    print(f'Chaves abertas:  {opens}')
    print(f'Chaves fechadas: {closes}')
    print(f'Balanco:         {opens - closes}  (deve ser 0)')
    bt = js.count('`')
    print(f'Backticks:       {bt} (par: {bt % 2 == 0})')
    # Procura erros obvios
    if opens != closes:
        print('\nAVISO: chaves desbalanceadas!')
    if bt % 2 != 0:
        print('AVISO: backticks desbalanceados!')
    else:
        print('\nJS parece sintaticamente OK para verificacao basica.')
