#!/usr/bin/env python3
"""Testa o login pelo 9Drive depois da mudança para redirect HTTPS + app publicado."""
import time

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9333")
    ctx = b.contexts[0]
    pg = ctx.new_page()
    erros = []
    pg.on("console", lambda m: erros.append(m.text[:120]) if m.type == "error" else None)
    pg.goto("http://9drive.localhost/", wait_until="domcontentloaded", timeout=60000)
    time.sleep(5)
    print("1) app:", pg.url[:50], "|", pg.title()[:28])

    if "login" in pg.url or "Entrar" in pg.evaluate("() => document.body.innerText")[:400]:
        pg.evaluate("""() => {
          const b = Array.from(document.querySelectorAll('button,a,[role=button]'))
            .find(e => /google/i.test(e.innerText||'') && e.getBoundingClientRect().width > 0);
          if (b) b.click();
        }""")
        time.sleep(10)
    print("2) depois do clique:", pg.url[:70])

    # percorre: aviso de app não verificado, escolha de conta, consentimento
    for passo in range(8):
        u = pg.url
        txt = pg.evaluate("() => document.body.innerText")
        print(f"   [{passo}] {u[:62]}")
        if "9drive.localhost" in u and "login" not in u:
            break
        clicou = pg.evaluate("""() => {
          const alvos = ['avançado','advanced','continuar','continue','permitir','allow',
                         'prosseguir','ir para','go to','aceitar','sim','confirmar'];
          const els = Array.from(document.querySelectorAll('button,[role=button],a,div[role=link]'))
            .filter(e => e.getBoundingClientRect().width > 0);
          for (const t of alvos) {
            const el = els.find(e => new RegExp('^' + t, 'i').test((e.innerText||'').trim()));
            if (el) { const nome = (el.innerText||'').trim().slice(0,28); el.click(); return nome; }
          }
          // link "Advanced" costuma ser um <a> com texto próprio
          const adv = els.find(e => /não verificado|unverified|avançado/i.test(e.innerText||''));
          if (adv) { const n = (adv.innerText||'').trim().slice(0,28); adv.click(); return n; }
          return null;
        }""")
        print("      clique:", clicou)
        if not clicou:
            time.sleep(4)
        else:
            time.sleep(6)

    time.sleep(6)
    print("FINAL:", pg.url[:80])
    txt = pg.evaluate("() => document.body.innerText")
    for l in [x.strip() for x in txt.splitlines() if x.strip()][:12]:
        print("   |", l[:85])
    if erros:
        print("erros de console:", [e for e in erros if "favicon" not in e][:3])
    pg.close(); b.close()
