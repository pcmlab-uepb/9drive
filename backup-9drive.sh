#!/usr/bin/env bash
# Backup diario do banco do 9drive para o Yandex.Disk (recuperacao em caso de perda do disco).
# Uso: bash backup-9drive.sh   (agendado no crontab do usuario)
set -euo pipefail

PROJ="/home/rodrigo/Yandex.Disk/Pesquisa/9drive"
ENVF="$PROJ/.env.docker"
# ATENCAO: a pasta Pesquisa esta em --exclude-dirs do daemon do Yandex.Disk
# (nao sobe para a nuvem). Por isso o backup vai para uma pasta de 1o nivel,
# que o daemon sincroniza de verdade — senao nao haveria copia recuperavel.
BKDIR="/home/rodrigo/Yandex.Disk/9drive-backups"
KEEP=14

mkdir -p "$BKDIR"
STAMP="$(date +%F_%H%M)"
OUT="$BKDIR/9drive_${STAMP}.sql.gz"

# senha do root do MySQL vem do .env.docker (nao fica no script)
DBPASS="$(grep -E '^MYSQL_ROOT_PASSWORD=' "$ENVF" | cut -d= -f2-)"

if ! docker ps --format '{{.Names}}' | grep -q '^9drive-mysql-1$'; then
  echo "$(date '+%F %T') ERRO: container 9drive-mysql-1 nao esta rodando" >&2
  exit 1
fi

docker exec 9drive-mysql-1 sh -c "exec mysqldump -u root -p'$DBPASS' --single-transaction --quick 9drive" \
  | gzip -9 > "$OUT"

# integridade minima: gzip valido e conteudo nao vazio
gzip -t "$OUT"
SIZE=$(stat -c%s "$OUT")
if [ "$SIZE" -lt 1000 ]; then
  echo "$(date '+%F %T') ERRO: backup suspeito (${SIZE} bytes)" >&2
  exit 1
fi

# retencao
ls -1t "$BKDIR"/9drive_*.sql.gz 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm -f

echo "$(date '+%F %T') OK ${OUT} (${SIZE} bytes)"
