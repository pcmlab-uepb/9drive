#!/usr/bin/env python3
"""Cliente OAuth: adiciona o redirect HTTPS e remove as entradas HTTP (exigência para publicar)."""
import time

from playwright.sync_api import sync_playwright

CLIENTE = ("https://console.cloud.google.com/auth/clients/"
           "813199353746-s3c83r1j5bvmadtngi32ia0tvg9slckk.apps.googleusercontent.com"
           "?project=fq2-materiais-261011")
NOVO_REDIRECT = "https://localhost/connected-accounts/google/callback"
REMOVER = ["http://localhost:5173", "http://localhost:4000/connected-accounts/google/callback"]

JS_ADD = """(nth) => {
  const btns = [];
  (function walk(root) {
    for (const el of root.querySelectorAll('*')) {
      if (el.tagName.toLowerCase() === 'button' && (el.innerText||'').trim() === 'Adicionar URI') btns.push(el);
      if (el.shadowRoot) walk(el.shadowRoot);
    }
  })(document);
  if (!btns[nth]) return 'sem botao ' + nth + ' (total ' + btns.length + ')';
  btns[nth].click(); return 'ok';
}"""

JS_VALS = """() => {
  const out = [];
  (function walk(root) {
    for (const el of root.querySelectorAll('*')) {
      const t = el.tagName.toLowerCase();
      if ((t === 'input' && el.type === 'text') || t === 'textarea') out.push(el.value || '');
      if (el.shadowRoot) walk(el.shadowRoot);
    }
  })(document);
  return out;
}"""

JS_APAGAR_LINHA = """(valor) => {
  let alvo = null;
  (function walk(root) {
    for (const el of root.querySelectorAll('*')) {
      const t = el.tagName.toLowerCase();
      if ((t === 'input' || t === 'textarea') && (el.value || '').trim() === valor) alvo = el;
      if (el.shadowRoot) walk(el.shadowRoot);
    }
  })(document);
  if (!alvo) return 'campo nao encontrado';
  // sobe procurando o container da linha e o botao de excluir dela
  let no = alvo;
  for (let nivel = 0; nivel < 8 && no; nivel++) {
    const btns = Array.from(no.querySelectorAll('button'))
      .filter(b => /excluir|remover|delete|remove/i.test((b.innerText || '') + ' ' + (b.getAttribute('aria-label') || '')));
    if (btns.length) { btns[btns.length - 1].click(); return 'cliquei nivel ' + nivel; }
    no = no.parentElement || (no.getRootNode && no.getRootNode().host);
  }
  return 'sem botao na linha';
}"""

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9333")
    pg = b.contexts[0].new_page()
    pg.bring_to_front()
    pg.goto(CLIENTE, wait_until="domcontentloaded", timeout=90000)
    time.sleep(9)
    for _ in range(4):
        pg.mouse.wheel(0, 500)
        time.sleep(0.4)
    print("antes:", [v for v in pg.evaluate(JS_VALS) if v])

    # 1) adiciona o redirect HTTPS (seção de URIs de redirecionamento = 2º "Adicionar URI")
    print("add:", pg.evaluate(JS_ADD, 1))
    time.sleep(2.5)
    pg.keyboard.type(NOVO_REDIRECT, delay=20)
    time.sleep(1.5)
    print("depois de add:", [v for v in pg.evaluate(JS_VALS) if v])

    # 2) remove as entradas HTTP
    for valor in REMOVER:
        r = pg.evaluate(JS_APAGAR_LINHA, valor)
        time.sleep(2)
        restam = [v for v in pg.evaluate(JS_VALS) if v]
        print(f"  remover {valor[:55]!r}: {r} | restam: {restam}")

    # 3) salva
    ok = pg.evaluate("""() => {
      const btns = Array.from(document.querySelectorAll('button,[role=button]'))
        .filter(e => e.getBoundingClientRect().width > 0 && /^(Salvar|Save)$/i.test((e.innerText||'').trim()));
      if (!btns.length) return 'sem botao salvar';
      btns[btns.length-1].click(); return 'cliquei salvar';
    }""")
    print("salvar:", ok)
    time.sleep(7)
    txt = pg.evaluate("() => document.body.innerText")
    for l in [x.strip() for x in txt.splitlines() if x.strip()]:
        if any(k in l.lower() for k in ("salv", "inválid", "erro", "obrigat", "https")):
            print("  |", l[:120])

    # 4) confere recarregando
    pg.goto(CLIENTE, wait_until="domcontentloaded", timeout=90000)
    time.sleep(9)
    print("=== persistido ===")
    for v in pg.evaluate(JS_VALS):
        if v:
            print("  ", v)
    pg.close(); b.close()
