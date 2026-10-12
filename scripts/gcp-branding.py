#!/usr/bin/env python3
"""Preenche as URLs (homepage + política) no Branding do Google Auth Platform e salva."""
import sys
import time

from playwright.sync_api import sync_playwright

HOME_URL = "https://pcmlab-uepb.github.io/9drive/"
PRIV_URL = "https://pcmlab-uepb.github.io/9drive/privacy.html"
DOMINIO = "pcmlab-uepb.github.io"
URL_PAG = "https://console.cloud.google.com/auth/branding?project=fq2-materiais-261011"


def ax(cdp):
    return cdp.send("Accessibility.getFullAXTree")["nodes"]


def achar(cdp, nome, role=None):
    for n in ax(cdp):
        r = (n.get("role") or {}).get("value", "")
        nm = (n.get("name") or {}).get("value", "")
        if nome.lower() in nm.lower() and n.get("backendDOMNodeId"):
            if role is None or r == role:
                return n["backendDOMNodeId"], r, nm
    return None, None, None


def clicar(cdp, pg, node_id):
    cdp.send("DOM.scrollIntoViewIfNeeded", {"backendNodeId": node_id})
    time.sleep(0.4)
    bm = cdp.send("DOM.getBoxModel", {"backendNodeId": node_id})["model"]
    q = bm["content"]
    x = (q[0] + q[2] + q[4] + q[6]) / 4
    y = (q[1] + q[3] + q[5] + q[7]) / 4
    pg.mouse.click(x, y)
    time.sleep(0.5)


def preencher(cdp, pg, rotulo, valor):
    _id, role, nome = achar(cdp, rotulo)
    if not _id:
        print(f"  ✗ campo não encontrado: {rotulo}")
        return False
    clicar(cdp, pg, _id)
    pg.keyboard.press("Control+a")
    pg.keyboard.press("Delete")
    pg.keyboard.type(valor, delay=18)
    time.sleep(0.8)
    print(f"  ✓ {nome[:45]!r} = {valor}")
    return True


with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9333")
    pg = b.contexts[0].new_page()
    pg.bring_to_front()
    pg.goto(URL_PAG, wait_until="domcontentloaded", timeout=90000)
    time.sleep(9)
    for _ in range(6):
        pg.mouse.wheel(0, 800)
        time.sleep(0.6)
    cdp = pg.context.new_cdp_session(pg)

    print("1) preenchendo URLs")
    preencher(cdp, pg, "Página inicial do aplicativo", HOME_URL)
    preencher(cdp, pg, "Política de Privacidade", PRIV_URL)

    print("2) domínio autorizado")
    # remove o 'lvh.me' que sobrou de um teste anterior
    for nit in range(4):
        _id, role, nome = achar(cdp, "Excluir item", role="button")
        if not _id:
            break
        # só remove se ainda existir domínio indesejado
        tem_lvh, _, _ = achar(cdp, "Domínio autorizado 1")
        valor_atual = None
        for n in ax(cdp):
            if "Domínio autorizado 1" in ((n.get("name") or {}).get("value", "")):
                valor_atual = (n.get("value") or {}).get("value", "")
        if valor_atual and valor_atual.strip() == DOMINIO:
            break
        print(f"   removendo domínio atual: {valor_atual!r}")
        clicar(cdp, pg, _id)
        time.sleep(1.2)
        break

    _id_add, _, _ = achar(cdp, "Adicionar domínio", role="button")
    if _id_add:
        clicar(cdp, pg, _id_add)
        time.sleep(1.5)
        vazios = []
        for n in ax(cdp):
            nm = (n.get("name") or {}).get("value", "")
            v = (n.get("value") or {}).get("value", "")
            if nm.startswith("Domínio autorizado") and not v and n.get("backendDOMNodeId"):
                vazios.append((n["backendDOMNodeId"], nm))
        if vazios:
            nid, nm = vazios[-1]
            clicar(cdp, pg, nid)
            pg.keyboard.type(DOMINIO, delay=18)
            time.sleep(1)
            print(f"  ✓ {nm} = {DOMINIO}")
        else:
            print("  ✗ não apareceu campo de domínio novo")

    print("3) salvando")
    _id_s, _, _ = achar(cdp, "Salvar", role="button")
    if _id_s:
        clicar(cdp, pg, _id_s)
        time.sleep(8)
    else:
        pg.evaluate("""() => {
          const b = Array.from(document.querySelectorAll('button,[role=button]'))
            .filter(e => (e.innerText||'').trim() === 'Salvar' && e.getBoundingClientRect().width > 0);
          if (b.length) b[b.length-1].click();
        }""")
        time.sleep(8)

    txt = pg.evaluate("() => document.body.innerText")
    print("--- estado após salvar ---")
    for l in [x.strip() for x in txt.splitlines() if x.strip()]:
        if any(k in l for k in ("Página inicial", "política", "Domínio", "erro", "inválid", "Salvo", "salv",
                                "github", "verific", "obrigat")):
            print("  |", l[:120])
    print("--- valores dos campos ---")
    for n in ax(cdp):
        role = (n.get("role") or {}).get("value", "")
        nm = (n.get("name") or {}).get("value", "")
        v = (n.get("value") or {}).get("value", "")
        if role in ("textbox", "combobox") and nm and v:
            print(f"  {nm[:50]!r} = {str(v)[:60]!r}")
    pg.close(); b.close()
