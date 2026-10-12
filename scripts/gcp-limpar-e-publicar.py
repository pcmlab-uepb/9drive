#!/usr/bin/env python3
"""Remove URIs HTTP inúteis (lvh.me) do cliente OAuth e tenta publicar o app."""
import time

from playwright.sync_api import sync_playwright

CLIENTE = ("https://console.cloud.google.com/auth/clients/"
           "813199353746-s3c83r1j5bvmadtngi32ia0tvg9slckk.apps.googleusercontent.com"
           "?project=fq2-materiais-261011")
PUBLICO = "https://console.cloud.google.com/auth/audience?project=fq2-materiais-261011"


def ax(cdp):
    return cdp.send("Accessibility.getFullAXTree")["nodes"]


def campos(cdp):
    out = []
    for n in ax(cdp):
        r = (n.get("role") or {}).get("value", "")
        if r in ("textbox",) and n.get("backendDOMNodeId"):
            out.append({"id": n["backendDOMNodeId"], "nome": (n.get("name") or {}).get("value", ""),
                        "val": (n.get("value") or {}).get("value", "")})
    return out


def botoes(cdp):
    out = []
    for n in ax(cdp):
        if (n.get("role") or {}).get("value") == "button" and n.get("backendDOMNodeId"):
            out.append({"id": n["backendDOMNodeId"], "nome": (n.get("name") or {}).get("value", "")})
    return out


def clicar(cdp, pg, node_id):
    cdp.send("DOM.scrollIntoViewIfNeeded", {"backendNodeId": node_id})
    time.sleep(0.4)
    m = cdp.send("DOM.getBoxModel", {"backendNodeId": node_id})["model"]["content"]
    pg.mouse.click((m[0] + m[2] + m[4] + m[6]) / 4, (m[1] + m[3] + m[5] + m[7]) / 4)
    time.sleep(0.8)


with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9333")
    pg = b.contexts[0].new_page()
    pg.bring_to_front()
    pg.goto(CLIENTE, wait_until="domcontentloaded", timeout=90000)
    time.sleep(9)
    for _ in range(4):
        pg.mouse.wheel(0, 500)
        time.sleep(0.4)
    cdp = pg.context.new_cdp_session(pg)

    print("=== URIs no cliente ===")
    for c in campos(cdp):
        if c["val"]:
            print(f"  {c['nome'][:42]!r} = {c['val'][:70]}")
    print("=== botões de remover ===")
    removs = [x for x in botoes(cdp) if "excluir" in x["nome"].lower() or "remover" in x["nome"].lower()]
    for x in removs:
        print("  ", x["nome"][:60])

    # remove os campos cujo valor contém lvh.me (na ordem inversa, para não bagunçar índices)
    alvos = [c for c in campos(cdp) if "lvh.me" in (c["val"] or "")]
    print(f"=== removendo {len(alvos)} campo(s) com lvh.me")
    for alvo in alvos:
        # acha o botão de remover mais próximo (mesmo container) pelo texto do botão
        removido = False
        for x in botoes(cdp):
            if "excluir" in x["nome"].lower() or "remover" in x["nome"].lower():
                clicar(cdp, pg, x["id"])
                time.sleep(1.5)
                # confere se o valor lvh.me sumiu
                restantes = [c["val"] for c in campos(cdp) if "lvh.me" in (c["val"] or "")]
                if not restantes:
                    print("  ✓ removido:", alvo["val"][:60])
                    removido = True
                    break
        if not removido:
            print("  ? não consegui remover:", alvo["val"][:60])
            break

    print("=== valores depois ===")
    for c in campos(cdp):
        if c["val"]:
            print(f"  {c['nome'][:42]!r} = {c['val'][:70]}")

    # salva
    for x in botoes(cdp):
        if x["nome"].strip().lower() in ("salvar", "save"):
            clicar(cdp, pg, x["id"])
            time.sleep(6)
            print("salvou cliente")
            break
    txt = pg.evaluate("() => document.body.innerText")
    for l in [x.strip() for x in txt.splitlines() if x.strip()]:
        if "salv" in l.lower() or "inválid" in l.lower() or "erro" in l.lower():
            print("  |", l[:120])

    print("=== tentando publicar ===")
    pg.goto(PUBLICO, wait_until="domcontentloaded", timeout=90000)
    time.sleep(9)
    cdp = pg.context.new_cdp_session(pg)
    for x in botoes(cdp):
        if "publicar app" in x["nome"].lower():
            clicar(cdp, pg, x["id"])
            time.sleep(4)
            break
    for rot in ("confirmar", "publicar", "sim"):
        for x in botoes(cdp):
            if x["nome"].strip().lower() == rot:
                clicar(cdp, pg, x["id"])
                time.sleep(6)
                break
        else:
            continue
        break
    txt = pg.evaluate("() => document.body.innerText")
    print("--- status ---")
    for l in [x.strip() for x in txt.splitlines() if x.strip()]:
        if any(k in l for k in ("Testando", "Em produção", "HTTPS", "publicar", "Status de publicação")):
            print("  |", l[:135])
    pg.close(); b.close()
