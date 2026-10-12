#!/usr/bin/env python3
"""Passo 2: conclui a conexão (autoriza no Google) e confere no banco quem está conectado.

Use depois que o usuário completar a credencial (senha/passkey/2FA) na janela do Chrome.
Uso:  python3 conectar-conta-passo2.py
"""
import subprocess
import time

from playwright.sync_api import sync_playwright

CDP = "http://127.0.0.1:9333"
ENVF = "/home/rodrigo/projetos/9drive/.env.docker"


def conectadas():
    pw = ""
    for linha in open(ENVF):
        if linha.startswith("MYSQL_ROOT_PASSWORD="):
            pw = linha.split("=", 1)[1].strip()
    out = subprocess.run(
        ["docker", "exec", "-e", f"MYSQL_PWD={pw}", "9drive-mysql-1", "mysql", "-u", "root", "9drive",
         "-e", "SELECT email, status FROM connected_accounts ORDER BY email;"],
        capture_output=True, text=True).stdout
    return [l for l in out.splitlines() if "@" in l]


with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(CDP)
    ctx = b.contexts[0]
    pg = next((x for x in ctx.pages if "accounts.google.com" in x.url), None)
    if pg is None:
        pg = next((x for x in ctx.pages if "localhost:4000" in x.url), None)
    if pg is None:
        print("nenhuma página do Google/callback aberta")
    else:
        pg.bring_to_front()
        for _ in range(5):
            print("  url:", pg.url[:80])
            if "localhost:4000" in pg.url and "error" not in pg.url:
                break
            r = pg.evaluate("""() => {
              const b = Array.from(document.querySelectorAll('button,[role=button],input[type=submit]'))
                .find(e => /continuar|continue|permitir|allow|aceitar|avançar/i.test(e.innerText || e.value || '')
                           && e.getBoundingClientRect().width > 0);
              if (!b) return null;
              const t = (b.innerText || b.value || '').trim().slice(0, 25);
              b.click();
              return t;
            }""")
            print("  clique:", r)
            if not r:
                time.sleep(4)
                continue
            time.sleep(7)
        time.sleep(6)
        txt = pg.evaluate("() => document.body.innerText")
        for l in [x.strip() for x in txt.splitlines() if x.strip()][:6]:
            print("  |", l[:90])
        print("  url final:", pg.url[:80])

    print("\ncontas conectadas no 9Drive:")
    for l in conectadas():
        print("  ", l)
    b.close()
