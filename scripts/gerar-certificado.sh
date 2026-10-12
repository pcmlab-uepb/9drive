#!/usr/bin/env bash
# Gera o certificado TLS local que o app usa no redirect do Google (https://localhost/...).
# Necessário para: (1) o app funcionar com HTTPS; (2) o Google permitir publicar o app
# (a publicação exige que TODAS as URIs de redirecionamento sejam HTTPS).
#
# Uso:  bash scripts/gerar-certificado.sh
# Rode de dentro do repositório (usa ./certs). A chave NUNCA deve ir para o git (certs/ está no .gitignore).
set -euo pipefail

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
CERTS="$REPO/certs"
mkdir -p "$CERTS"

if [ -f "$CERTS/localhost.crt" ] && [ "${1:-}" != "--forcar" ]; then
  echo "certificado já existe em $CERTS (use --forcar para regerar)"
else
  openssl req -x509 -newkey rsa:2048 -nodes -days 825 \
    -keyout "$CERTS/localhost.key" -out "$CERTS/localhost.crt" \
    -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:9drive.localhost,IP:127.0.0.1"
  chmod 600 "$CERTS/localhost.key"
  echo "certificado gerado: $CERTS/localhost.crt"
fi

# Confia no certificado pelo menos no NSS do usuário (Chrome/Chromium) — não exige root.
if command -v certutil >/dev/null 2>&1; then
  mkdir -p "$HOME/.pki/nssdb"
  certutil -d sql:"$HOME/.pki/nssdb" -A -t "C,," -n "9drive-local" -i "$CERTS/localhost.crt" \
    && echo "confiado no NSS do usuário (Chrome)"
  for db in "$HOME"/.zen/*/cert9.db "$HOME"/.mozilla/firefox/*/cert9.db; do
    [ -f "$db" ] || continue
    certutil -d sql:"$(dirname "$db")" -A -t "C,," -n "9drive-local" -i "$CERTS/localhost.crt" 2>/dev/null \
      && echo "confiado em $(dirname "$db")"
  done
else
  echo "aviso: certutil ausente — o navegador vai pedir para aceitar o certificado uma vez"
fi

echo
echo "Depois disso: docker compose --env-file .env.docker up -d frontend backend"
echo "Teste:      curl -s https://localhost/health"
