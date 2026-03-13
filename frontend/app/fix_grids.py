import re

files = [
    'src/pages/DashboardCliente.jsx',
    'src/pages/DashboardAdmin.jsx',
]

def refactor_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace specific gridTemplateColumns strings and inject class className properly
    
    content = content.replace("display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 120px',", "")
    content = content.replace("display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 100px',", "")
    content = content.replace("display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr 100px',", "")
    content = content.replace("display: 'grid', gridTemplateColumns: '3fr 1fr 1fr 1fr 1fr 120px',", "")
    
    content = content.replace("gridTemplateColumns: 'repeat(4, 1fr)'", "gridTemplateColumns: 'repeat(4, 1fr)'") # just in case
    
    # We will just inject the classes where needed.
    
    # Simple regex replacing typical grid configurations in style objects
    content = re.sub(
        r'<div style={{ display: \'grid\', gridTemplateColumns: \'repeat\(4, 1fr\)\', gap: 16 }}>',
        r'<div className="dashboard-grid-4" style={{ gap: 16 }}>',
        content
    )
    content = re.sub(
        r'<div style={{ display: \'grid\', gridTemplateColumns: \'repeat\(4, 1fr\)\', gap: 24, marginBottom: 24 }}>',
        r'<div className="dashboard-grid-4" style={{ gap: 24, marginBottom: 24 }}>',
        content
    )
    content = re.sub(
        r'<div style={{ display: \'grid\', gridTemplateColumns: \'repeat\(3, 1fr\)\', gap: 16 }}>',
        r'<div className="dashboard-grid-3" style={{ gap: 16 }}>',
        content
    )
    content = re.sub(
        r'<div style={{ display: \'grid\', gridTemplateColumns: \'repeat\(3, 1fr\)\', gap: 16, marginBottom: 16 }}>',
        r'<div className="dashboard-grid-3" style={{ gap: 16, marginBottom: 16 }}>',
        content
    )
    content = re.sub(
        r'<div style={{ display: \'grid\', gridTemplateColumns: \'1\.5fr 1fr 1fr\', gap: 16, marginBottom: 16 }}>',
        r'<div className="dashboard-grid-3" style={{ gridTemplateColumns: \'1.5fr 1fr 1fr\', gap: 16, marginBottom: 16 }}>',
        content
    )
    content = re.sub(
        r'<div style={{ display: \'grid\', gridTemplateColumns: \'repeat\(2, 1fr\)\', gap: 16 }}>',
        r'<div className="dashboard-grid-2" style={{ gap: 16 }}>',
        content
    )

    # For grid-5 or tables that we removed the grid style, we need to add the className
    content = re.sub(
        r'<div style={{\s+background: \'#060908\', padding: \'16px 20px\',',
        r'<div className="dashboard-grid-5 hide-mobile" style={{ background: \'#060908\', padding: \'16px 20px\',',
        content
    )
    content = re.sub(
        r'(<div[^>]*)(style={{\s+padding: \'16px 20px\', alignItems: \'center\',)',
        r'\1className="dashboard-grid-5" \2',
        content
    )
    
    # Pointers to add responsive classes to tabs or general padding
    if "className=" not in content:
        # Just to track
        pass
        
    content = re.sub(
        r'(<div style={{ padding: \'36px 40px\', maxWidth: 1320, margin: \'0 auto\' }})',
        r'<div className="p-mobile" style={{ padding: \'36px 40px\', maxWidth: 1320, margin: \'0 auto\' }}',
        content
    )
    
    content = re.sub(
        r'<div style={{ display: \'flex\', borderBottom: \'1px solid #1A2A1C\', background: \'#0A0F0B\', padding: \'0 40px\', overflowX: \'auto\' }}>',
        r'<div className="mobile-tabs" style={{ display: \'flex\', borderBottom: \'1px solid #1A2A1C\', background: \'#0A0F0B\', padding: \'0 40px\', overflowX: \'auto\', whiteSpace: \'nowrap\' }}>',
        content
    )

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

for file in files:
    try:
        refactor_file(file)
        print("Success on", file)
    except Exception as e:
        print("Error on", file, str(e))
