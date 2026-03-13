with open('src/pages/DashboardAdmin.jsx', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace("\\'", "'")
with open('src/pages/DashboardAdmin.jsx', 'w', encoding='utf-8') as f:
    f.write(text)

with open('src/pages/DashboardCliente.jsx', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace("\\'", "'")
with open('src/pages/DashboardCliente.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
print("Done")
