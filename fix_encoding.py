# fix_encoding_final.py
# Corrige double-encoding em arquivo UTF-8 que foi salvo incorretamente pelo PowerShell
# Os chars Unicode 0x80-0xFF no arquivo sao bytes UTF-8 interpretados como codepoints individuais

FILE = r"C:\Users\lenov\MFL_Digital_Solutions\frontend\dashboards\dashboard_completo_html.html"

with open(FILE, encoding='utf-8') as f:
    content = f.read()

print(f"Arquivo lido: {len(content)} chars")

# Converte os codepoints 0x00-0xFF de volta para bytes e decodifica como UTF-8
# Processa char a char, coletando sequencias de bytes (codepoints <= 0xFF)
result = []
i = 0
fixed_count = 0

while i < len(content):
    cp = ord(content[i])
    
    if cp <= 0x7F:
        # ASCII - nao corrompido
        result.append(content[i])
        i += 1
    elif cp <= 0xFF:
        # Possivelmente inicio de sequencia multi-byte corrompida
        # Coleta bytes consecutivos (codepoints <= 0xFF)
        byte_seq = []
        j = i
        while j < len(content) and ord(content[j]) <= 0xFF:
            byte_seq.append(ord(content[j]))
            j += 1
        
        # Tenta decodificar como UTF-8 progressivamente
        decoded_str = ''
        k = 0
        while k < len(byte_seq):
            # Determina quantos bytes este codepoint UTF-8 precisa
            b = byte_seq[k]
            if b < 0x80:
                n = 1
            elif b < 0xC0:
                # Byte de continuacao solto - erro
                decoded_str += chr(b)
                k += 1
                continue
            elif b < 0xE0:
                n = 2
            elif b < 0xF0:
                n = 3
            else:
                n = 4
            
            if k + n <= len(byte_seq):
                try:
                    chunk = bytes(byte_seq[k:k+n])
                    decoded_str += chunk.decode('utf-8')
                    fixed_count += n - 1
                    k += n
                except UnicodeDecodeError:
                    decoded_str += chr(byte_seq[k])
                    k += 1
            else:
                decoded_str += chr(byte_seq[k])
                k += 1
        
        result.append(decoded_str)
        i = j
    else:
        # Char Unicode acima de 0xFF - ja esta correto (emojis proprios, chars CJK, etc)
        result.append(content[i])
        i += 1

fixed = ''.join(result)

print(f"Corrigidos: {fixed_count} bytes re-agrupados")
print(f"Resultado: {len(fixed)} chars")

# Salva
with open(FILE, 'w', encoding='utf-8', newline='\n') as f:
    f.write(fixed)

print("Arquivo salvo!")

# Verificacao
still_bad = sum(1 for c in fixed if 0xC0 <= ord(c) <= 0xFF)
print(f"Chars ainda suspeitos: {still_bad}")

checks = [
    ("\u00f0\u009f\u0094\u008a", "AINDA CORROMPIDO (emoji nao corrigido)"),  # ðŸ"Š
    ("\U0001f4ca", "Grafico OK"),   # 📊
    ("Imobili\u00e1ria", "Port. OK"),
    ("renderClientTab", "JS OK"),
    ("aten\u00e7\u00e3o", "Port OK 2"),
]
for chk, label in checks:
    found = chk in fixed
    print(f"  {'ENCONTROU' if found else 'NAO ENCONTROU'} {label}")
