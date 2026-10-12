#!/usr/bin/env python3
"""Publica o app OAuth (sai do modo Testando) e confirma o status."""
import time

from playwright.sync_api import sync_playwright

URL = "https://console.cloud.google.com/auth/audience?project=fq2-materiais-261011"


def ax(cdp):
    return cdp.send("Accessibility.getFullAXTree")["nodes"]


def achar_btn(cdp, texto):
    for n in ax(cdp):
        if (n.get("role") or {}).get("value") == "button":
            nm = (n.get("name") or {}).get("value", "")
            if texto.lower() in nm.lower() and n.get("backendDOMNodeId"):
                return n["backendDOMNodeId"], nm
    return None, None


def clicar(cdp, pg, node_id):
    cdp.send("DOM.scrollIntoViewIfNeeded", {"backendNodeId": node_id})
    time.sleep(0.4)
    m = cdp.send("DOM.getBoxModel", {"backendNodeId": node_id})["model"]["content"]
    pg.mouse.click((m[0] + m[2] + m[4] + m[6]) / 4, (m[1] + m[3] + m[5] + m[7]) / 4)
    time.sleep(0.6)


with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9333")
    pg = b.contexts[0].new_page()
    pg.bring_to_front()
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(9)
    cdp = pg.context.new_cdp_session(pg)

    txt = pg.evaluate("() => document.body.innerText")
    print("--- status antes ---")
    for l in [x.strip() for x in txt.splitlines() if x.strip()]:
        if any(k in l for k in ("Status de publicação", "Testando", "Em produção", "usuários de teste", "Publicar")):
            print("  |", l[:120])

    _id, nome = achar_btn(cdp, "Publicar app")
    print("botão:", nome)
    if _id:
        clicar(cdp, pg, _id)
        time.sleep(4)
        txtdlg = pg.evaluate("() => document.body.innerText")
        print("--- diálogo ---")
        for l in [x.strip() for x in txtdlg.splitlines() if x.strip()]:
            if any(k in l.lower() for k in ("publicar", "confirmar", "produção", "verifica", "política", "logotipo", "cancelar")):
                print("  |", l[:130])
        for rotulo in ("Confirmar", "Publicar", "Sim", "Continuar"):
            _idc, nomec = achar_btn(cdp, rotulo)
            if _idc:
                print("clicando:", nomec)
                clicar(cdp, pg, _idc)
                time.sleep(6)
                break

    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    txt = pg.evaluate("() => document.body.innerText")
    print("--- status depois ---")
    for l in [x.strip() for x in txt.splitlines() if x.strip()]:
        if any(k in l for k in ("Status de publicação", "Testando", "Em produção", "usuários de teste", "Público-alvo")):
            print("  |", l[:130])
    pg.close(); b.close()
