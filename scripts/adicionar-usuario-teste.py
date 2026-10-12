#!/usr/bin/env python3
"""Acrescenta um e-mail à lista de Usuários de teste do Google Auth Platform."""
import sys, time
from playwright.sync_api import sync_playwright

EMAIL = sys.argv[1] if len(sys.argv) > 1 else ""
if not EMAIL:
    raise SystemExit("uso: adicionar-usuario-teste.py <email>")

FIND = """() => {
  const out = [];
  function walk(root, d) {
    if (d > 12) return;
    for (const el of root.querySelectorAll('*')) {
      if (el.tagName.toLowerCase() === 'input' && !el.disabled) {
        const r = el.getBoundingClientRect();
        if (r.width > 80 && r.height > 10) out.push({x: r.x + r.width/2, y: r.y + r.height/2, aria: el.getAttribute('aria-label')||''});
      }
      if (el.shadowRoot) walk(el.shadowRoot, d + 1);
    }
  }
  walk(document, 0); return out;
}"""

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9333")
    ctx = b.contexts[0]
    pg = ctx.new_page()
    pg.goto("https://console.cloud.google.com/auth/audience?project=fq2-materiais-261011",
            wait_until="domcontentloaded", timeout=90000)
    time.sleep(7)

    antes = pg.evaluate("() => document.body.innerText")
    if EMAIL in antes:
        print(f"{EMAIL} já está na lista ✓")
        pg.close(); b.close(); raise SystemExit(0)

    pg.evaluate("""() => {
      const els = Array.from(document.querySelectorAll('button,a,[role=button]'))
        .filter(e => e.getBoundingClientRect().width > 0 && /^(Add users|Adicionar usu)/i.test((e.innerText||'').trim()));
      if (els.length) els[els.length-1].click();
    }""")
    time.sleep(4)
    campo = next((c for c in pg.evaluate(FIND) if "e-mail" in (c["aria"] or "").lower()), None)
    if not campo:
        print("não achei o campo de e-mails (o diálogo abriu?)")
        pg.close(); b.close(); raise SystemExit(1)
    pg.mouse.click(campo["x"], campo["y"]); time.sleep(0.5)
    pg.keyboard.type(EMAIL, delay=22)
    pg.keyboard.press(",")          # força virar "chip"
    time.sleep(1)
    print("salvar:", pg.evaluate("""() => {
      const btns = Array.from(document.querySelectorAll('button,[role=button]'))
        .filter(e => e.getBoundingClientRect().width > 0 && /^(Salvar|Save|Adicionar|Add)$/i.test((e.innerText||'').trim()));
      if (!btns.length) return 'sem botão salvar';
      btns[btns.length-1].click(); return 'clicou';
    }"""))
    time.sleep(6)
    txt = pg.evaluate("() => document.body.innerText")
    for l in [x.strip() for x in txt.splitlines() if x.strip()]:
        if "usuário" in l.lower() or "@" in l:
            print("  |", l[:95])
    pg.close(); b.close()
