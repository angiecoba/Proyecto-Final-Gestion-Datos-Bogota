import subprocess, os
os.makedirs('out/img', exist_ok=True)
INK, MUTED, LINE = '#1F2A37', '#5B6676', '#9AA4B2'
TEAL, TEAL_BG, AMBER_BG, GRAY_BG = '#0F5C63', '#E3F0F0', '#FBF0DA', '#F2F4F7'
FONT = 'Inter'

def render(name, dot):
    open(f'out/img/{name}.dot', 'w').write(dot)
    subprocess.run(['dot', '-Tpng', '-Gdpi=220', f'out/img/{name}.dot', '-o', f'out/img/{name}.png'], check=True)
    subprocess.run(['dot', '-Tsvg', f'out/img/{name}.dot', '-o', f'out/img/{name}.svg'], check=True)

def table(name, cols, color=TEAL, bg='white'):
    rows = ''.join(
        f'<TR><TD ALIGN="LEFT" BALIGN="LEFT" PORT="{c[0]}"><FONT COLOR="{INK if c[2] else MUTED}">'
        f'{"<B>" if c[2]=="PK" else ""}{c[0]}{"</B>" if c[2]=="PK" else ""}</FONT></TD>'
        f'<TD ALIGN="LEFT"><FONT COLOR="{MUTED}" POINT-SIZE="10">{c[1]}</FONT></TD>'
        + (f'<TD ALIGN="CENTER"><FONT COLOR="{TEAL if c[2]=="PK" else "#B45309"}" POINT-SIZE="9.5"><B>{c[2]}</B></FONT></TD></TR>' if c[2] else '<TD> </TD></TR>')
        for c in cols)
    return (f'{name} [shape=plain, label=<<TABLE BORDER="1" COLOR="{LINE}" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="{bg}">'
            f'<TR><TD COLSPAN="3" BGCOLOR="{color}"><FONT COLOR="white"><B>{name}</B></FONT></TD></TR>{rows}</TABLE>>];')

