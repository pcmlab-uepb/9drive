#!/usr/bin/env python3
"""Teste de upload do 9Drive de ponta a ponta, como o usuário REAL.

Assina um access token com o segredo do próprio app (JWT_ACCESS_SECRET) para a sessão web válida,
envia um arquivo pequeno pelo endpoint resumable, confere em qual conta conectada ele caiu e apaga
(inclusive no Google Drive). Também limpa o usuário de teste criado por engano antes.
"""
import base64
import hashlib
import hmac
import json
import subprocess
import time
import urllib.error
import urllib.request

PROJ = "/home/rodrigo/projetos/9drive"
API = "http://localhost:4000"
NOME_ARQ = "teste-hermes-9drive.txt"
CONTEUDO = ("Teste de upload do pool 9Drive (Hermes). Pode apagar.\n" + ("enchimento 0123456789\n" * 70)).encode()


def env():
    d = {}
    for linha in open(f"{PROJ}/.env.docker"):
        if "=" in linha and not linha.startswith("#"):
            k, v = linha.rstrip("\n").split("=", 1)
            d[k] = v
    return d


def sql(query):
    e = env()
    return subprocess.run(["docker", "exec", "-e", f"MYSQL_PWD={e['MYSQL_ROOT_PASSWORD']}", "9drive-mysql-1",
                           "mysql", "-u", "root", "9drive", "-N", "-B", "-e", query],
                          capture_output=True, text=True).stdout.strip()


def b64u(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=")


def mint(segredo, sub, sid):
    header = b64u(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = b64u(json.dumps({"sub": sub, "sid": sid,
                               "iat": int(time.time()), "exp": int(time.time()) + 3600}).encode())
    assin = b64u(hmac.new(segredo.encode(), header + b"." + payload, hashlib.sha256).digest())
    return (header + b"." + payload + b"." + assin).decode()


def req(method, url, data=None, tok=None, raw=False, extra=None):
    h = {"Content-Type": "application/octet-stream" if raw else "application/json"}
    h.update(extra or {})
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    body = data if raw else (json.dumps(data).encode() if data is not None else None)
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            txt = resp.read().decode(errors="replace")
            try:
                return resp.status, json.loads(txt)
            except Exception:
                return resp.status, txt
    except urllib.error.HTTPError as e:
        txt = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(txt)
        except Exception:
            return e.code, txt


E = env()
linha = sql("SELECT u.id, s.id FROM users u JOIN user_sessions s ON s.user_id=u.id "
            "WHERE s.revoked_at IS NULL AND s.expires_at > NOW() AND u.email LIKE '%@servidor.uepb.edu.br' "
            "ORDER BY s.created_at DESC LIMIT 1;")
if not linha:
    raise SystemExit("não achei sessão válida do usuário real")
uid, sid = linha.split("\t")
tok = mint(E["JWT_ACCESS_SECRET"], uid, sid)

st, me = req("GET", f"{API}/auth/me", tok=tok)
print("1) identidade:", st, str(me)[:130])

st, ini = req("POST", f"{API}/uploads/resumable/init",
              {"fileName": NOME_ARQ, "mimeType": "text/plain", "sizeBytes": str(len(CONTEUDO))}, tok)
print("2) init:", st, json.dumps(ini, ensure_ascii=False)[:220] if isinstance(ini, dict) else ini)
sid_up = ini.get("sessionId") if isinstance(ini, dict) else None
if not sid_up:
    raise SystemExit(1)

st, fim = req("PUT", f"{API}/uploads/resumable/chunk/{sid_up}", CONTEUDO, tok, raw=True,
              extra={"Content-Range": f"bytes 0-{len(CONTEUDO)-1}/{len(CONTEUDO)}",
                     "Content-Length": str(len(CONTEUDO))})
print("3) envio do blob:", st, json.dumps(fim, ensure_ascii=False)[:250] if isinstance(fim, dict) else fim)

time.sleep(3)
print("4) onde caiu (banco):")
print("   " + sql("SELECT f.name, f.size_bytes, f.status, LEFT(f.provider_file_id,18), a.email FROM files f "
                  "LEFT JOIN connected_accounts a ON a.id=f.connected_account_id "
                  f"WHERE f.name='{NOME_ARQ}' ORDER BY f.created_at DESC LIMIT 1;").replace("\t", " | "))

fid = sql(f"SELECT id FROM files WHERE name='{NOME_ARQ}' ORDER BY created_at DESC LIMIT 1;")
if fid:
    st, r = req("DELETE", f"{API}/files/batch/permanent", {"fileIds": [fid]}, tok)
    print("5) apaguei (Drive incluso):", st, str(r)[:120])
    time.sleep(2)
    print("6) sobraram registros?", sql(f"SELECT COUNT(*) FROM files WHERE name='{NOME_ARQ}';"))

sql("DELETE FROM user_sessions WHERE user_id IN (SELECT id FROM users WHERE email='teste.upload.hermes@gmail.com');")
sql("DELETE FROM users WHERE email='teste.upload.hermes@gmail.com';")
print("7) usuário de teste removido:",
      sql("SELECT COUNT(*) FROM users WHERE email='teste.upload.hermes@gmail.com';"))
