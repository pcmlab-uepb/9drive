#!/usr/bin/env python3
"""Cria um cliente OAuth tipo Desktop para o rclone e baixa o JSON das credenciais."""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

CRIAR = "https://console.cloud.google.com/auth/clients/create?project=fq2-materiais-261011"
NOME = "rclone-9drive"
DESTINO = Path("/home/rodrigo/.config/rclone/gcp-desktop-client.json")

JS_LIMPAR = """() => {
  let vazios = [];
  (function walk(root) {
    for (const el of root.querySelectorAll('*')) {
      const t = el.tagName.toLowerCase();
      if ((t === 'input' && el.type === 'text') || t === 'textarea') {
        const r = el.getBoundingClientRect();
        if (r.width > 100) vazios.push(el.value || '');
      }
      if (el.shadowRoot) walk(el.shadowRoot);
    }
  })(document);
  return vazios;
}"""

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9333")
    pg = b.contexts[0].new_page()
    pg.bring_to_front()
    pg.goto(CRIAR, wait_until="domcontentloaded", timeout=90000)
    time.sleep(9)
    print("1) página:", pg.url[:80])
    txt = pg.evaluate("() => document.body.innerText")
    for l in [x.strip() for x in txt.splitlines() if x.strip()][:14]:
        print("   |", l[:95])

    # escolhe o tipo "Aplicativo de computador" (Desktop)
    r = pg.evaluate("""() => {
      const els = Array.from(document.querySelectorAll('div,span,label,li,[role=radio],[role=option],[role=menuitem]'))
        .filter(e => /aplicativo de computador|desktop app/i.test((e.innerText||'').trim()) && e.getBoundingClientRect().width > 30);
      if (!els.length) return null;
      const el = els[els.length-1]; const rc = el.getBoundingClientRect();
      return {x: rc.x + rc.width/2, y: rc.y + rc.height/2, texto: (el.innerText||'').trim().slice(0,40)};
    }""")
    print("2) tipo Desktop:", r)
    if r:
        pg.mouse.click(r["x"], r["y"])
        time.sleep(2.5)

    # nome
    campo = pg.evaluate("""() => {
      const out = [];
      (function walk(root) {
        for (const el of root.querySelectorAll('*')) {
          const t = el.tagName.toLowerCase();
          if ((t === 'input' && el.type === 'text') || t === 'textarea') {
            const rc = el.getBoundingClientRect();
            if (rc.width > 100) out.push({x: rc.x + rc.width/2, y: rc.y + rc.height/2, val: el.value || ''});
          }
          if (el.shadowRoot) walk(el.shadowRoot);
        }
      })(document);
      return out;
    }""")
    print("3) campos:", [c["val"] for c in campo])
    if campo:
        alvo = campo[0]
        pg.mouse.click(alvo["x"], alvo["y"])
        pg.keyboard.type(NOME, delay=18)
        time.sleep(1)

    # criar
    print("4) criar:", pg.evaluate("""() => {
      const b = Array.from(document.querySelectorAll('button,[role=button]'))
        .filter(e => /^(Criar|Create)$/i.test((e.innerText||'').trim()) && e.getBoundingClientRect().width > 0);
      if (!b.length) return 'sem botão criar';
      b[b.length-1].click(); return 'clicou';
    }"""))
    time.sleep(9)
    print("5) url:", pg.url[:100])
    txt = pg.evaluate("() => document.body.innerText")
    for l in [x.strip() for x in txt.splitlines() if x.strip()][:18]:
        print("   |", l[:100])

    # baixa o JSON das credenciais
    try:
        with pg.expect_download(timeout=15000) as dl:
            print("6) download:", pg.evaluate("""() => {
              const b = Array.from(document.querySelectorAll('button,[role=button],a'))
                .filter(e => /download|baixar|json/i.test((e.innerText||'') + ' ' + (e.getAttribute('aria-label')||'')) && e.getBoundingClientRect().width > 0);
              if (!b.length) return 'sem botão de download';
              b[b.length-1].click(); return 'clicou download';
            }"""))
        d = dl.value
        DESTINO.parent.mkdir(parents=True, exist_ok=True)
        d.save_as(str(DESTINO))
        dados = json.loads(Path(DESTINO).read_text())
        print("7) JSON salvo:", DESTINO, "| tipo:", dados.get("installed", dados).get("client_id", "")[:30] + "...")
    except Exception as e:
        print("7) download falhou:", str(e)[:120])
    pg.close(); b.close()
