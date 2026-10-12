#!/usr/bin/env python3
"""Abre a conexão de uma conta Google no 9Drive e conduz até a tela de credencial.

O que ele faz sozinho: pega a URL de consentimento com o token da sessão do painel, abre o Google,
escolhe "Usar outra conta" e digita o e-mail (identificador, não é segredo).
O que ele NÃO faz (de propósito): nunca digita senha, passkey ou código 2FA — o usuário completa na
janela do Chrome que fica em primeiro plano.

Uso:  python3 conectar-conta-passo1.py <email-da-conta>
Depois que o usuário entrar, rode o passo 2 (conectar-conta-passo2.py) para autorizar e conferir.
"""
import sys
import time

from playwright.sync_api import sync_playwright

EMAIL = sys.argv[1] if len(sys.argv) > 1 else ""
APP = "http://9drive.localhost"
CDP = "http://127.0.0.1:9333"

if not EMAIL:
    raise SystemExit("uso: conectar-conta-passo1.py <email-da-conta>")

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(CDP)
    ctx = b.contexts[0]
    for pg in list(ctx.pages):                      # limpa abas antigas de login/callback
        if "accounts.google.com" in pg.url or "localhost:4000" in pg.url:
            try:
                pg.close()
            except Exception:
                pass
    pg = ctx.new_page()
    pg.bring_to_front()
    pg.goto(f"{APP}/quota", wait_until="domcontentloaded", timeout=60000)
    time.sleep(5)

    url = pg.evaluate("""async () => {
      const tok = localStorage.getItem('9drive.accessToken');
      if (!tok) return 'SEM_TOKEN';
      const r = await fetch('/api/connected-accounts/google/connect-url',
                            {headers: {Authorization: 'Bearer ' + tok}});
      if (!r.ok) return 'HTTP ' + r.status;
      return (await r.json()).url || 'SEM_URL';
    }""")
    if not str(url).startswith("http"):
        raise SystemExit(f"não consegui a URL de conexão ({url}) — faça login no painel e repita")

    pg.goto(url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(6)

    # se aparecer o seletor de contas, escolhe "Usar outra conta"
    escolha = pg.evaluate("""() => {
      const els = Array.from(document.querySelectorAll('div,li,span,a,[role=link],[role=button]'))
        .filter(e => /usar outra conta|use another account/i.test(e.innerText || '')
                     && e.getBoundingClientRect().width > 40);
      if (!els.length) return null;
      const rc = els[els.length - 1].getBoundingClientRect();
      return {x: rc.x + rc.width / 2, y: rc.y + rc.height / 2};
    }""")
    if escolha:
        pg.mouse.click(escolha["x"], escolha["y"])
        time.sleep(6)

    # digita o e-mail no campo de identificação (se houver)
    campo = pg.evaluate("""() => {
      const el = document.querySelector('input[name=identifier], input[type=email]');
      if (!el) return null;
      const rc = el.getBoundingClientRect();
      return {x: rc.x + rc.width / 2, y: rc.y + rc.height / 2};
    }""")
    if campo:
        pg.mouse.click(campo["x"], campo["y"])
        time.sleep(0.5)
        pg.keyboard.type(EMAIL, delay=22)
        time.sleep(0.8)
        pg.keyboard.press("Enter")
        time.sleep(8)

    campos = pg.evaluate("""() => Array.from(document.querySelectorAll('input'))
        .filter(e => e.getBoundingClientRect().width > 40).map(e => e.type + '/' + (e.name || e.id || ''))""")
    txt = pg.evaluate("() => document.body.innerText")
    linhas = [x.strip() for x in txt.splitlines() if x.strip()]
    pendente = any(c.startswith("password") for c in campos) or any(
        "chave de acesso" in l or "passkey" in l.lower() or "Verificando sua identidade" in l for l in linhas)
    print("página:", pg.url[:70])
    for l in linhas[:8]:
        print("  |", l[:85])
    print(">>>", "CREDENCIAL NECESSÁRIA — complete na janela do Chrome" if pendente
          else "sem pedido de credencial (prossiga com o passo 2)")
    pg.bring_to_front()
    b.close()
