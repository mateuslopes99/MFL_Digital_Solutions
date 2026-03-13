# scan_corrupt.py - Encontra todos os caracteres corrompidos por double-encoding no arquivo
FILE = r"C:\Users\lenov\MFL_Digital_Solutions\frontend\dashboards\dashboard_completo_html.html"

with open(FILE, encoding='utf-8') as f:
    lines = f.readlines()

# Caracteres que indicam double-encoding (resultado de UTF-8 lido como latin-1)
# Range 0xC0-0xFF sao bytes iniciais de sequencias multi-byte UTF-8
# Quando lidos como latin-1 ficam como chars individuais nesse range

# Marcadores comuns de double-encoding que causam erros JS
CORRUPT_MARKERS = [
    '\u00e2\u20ac',  # â€  - prefixo de muitos chars especiais
    '\u00c3',       # Ã   - prefixo de chars portugueses (se ainda existir)
    '\u00e2\u009c',  # âœ  - checkmark area
    '\u00e2\u009a',  # âš  - warning/gear area  
    '\u00e2\u0080',  # â€  - quotes/dashes area
    '\u00f0\u0178',  # ðŸ  - emoji area (4-byte emoji corrupted) 
    '\u00e2\u201e',  # â„  - snowflake area
    '\u00f0\u0178\u0178',  # ðŸŸ - colored circle area
]

print(f"Total linhas: {len(lines)}")
print("\nLinhas com possiveis corrupcoes:")
corrupt_count = 0
for i, line in enumerate(lines, 1):
    has_corrupt = any(marker in line for marker in CORRUPT_MARKERS)
    # Verifica chars no range C0-FF que ainda existem
    bad_chars = [c for c in line if 0xC0 <= ord(c) <= 0xFF and ord(c) not in [0xC3, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9, 0xCA, 0xCB, 0xCC, 0xCD, 0xCE, 0xCF, 0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD8, 0xD9, 0xDA, 0xDB, 0xDC, 0xDD, 0xDE, 0xDF, 0xE0, 0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xEB, 0xEC, 0xED, 0xEE, 0xEF, 0xF0, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE]]
    if has_corrupt or (bad_chars and i > 1099):  # Foca nas linhas de JS
        print(f"  Linha {i:4d}: {repr(line[:100])}")
        corrupt_count += 1
        if corrupt_count > 30:
            print("  ... (muitas mais)")
            break

print(f"\nTotal de linhas corrompidas encontradas: {corrupt_count}")
