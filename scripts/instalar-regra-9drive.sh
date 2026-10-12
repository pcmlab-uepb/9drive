#!/usr/bin/env bash
# Instala/atualiza a REGRA 9Drive em TODOS os arquivos de regras do harness.
# Idempotente: o bloco fica entre os marcadores REGRA-9DRIVE:inicio / REGRA-9DRIVE:fim.
# Uso:  bash scripts/instalar-regra-9drive.sh [--dry-run]
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO="$(dirname "$SCRIPT_DIR")"
CANON="$REPO/docs/REGRA-9DRIVE.md"
DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

if [ ! -f "$CANON" ]; then
  echo "ERRO: não encontrei $CANON" >&2
  exit 1
fi

# --- alvos: todas as raízes de regras do harness ---
alvos=(
  "$HOME/AGENTS.md"
  "$HOME/.hermes/AGENTS.md"
  "$HOME/.config/opencode/AGENTS.md"
  "$HOME/.config/opencode/INSTRUCTIONS.md"
  "$HOME/.config/opencode/MCP-SETUP.md"
)
for g in "$HOME/rules"/*.md "$HOME/.config/opencode/rules"/*.md "$HOME/.claude/CLAUDE.md"; do
  [ -f "$g" ] && alvos+=("$g")
done

echo "REGRA 9Drive — instalando em ${#alvos[@]} arquivo(s)$([ "$DRY" = 1 ] && echo ' [dry-run]')"
instalados=0; criados=0; semmudanca=0

for f in "${alvos[@]}"; do
  if [ ! -f "$f" ]; then
    echo "  · inexistente, pulando: $f"
    continue
  fi
  antes="$(md5sum < "$f")"
  if [ "$DRY" = 1 ]; then
    python3 - "$f" "$CANON" <<'PY'
import pathlib, sys
f, canon = sys.argv[1], sys.argv[2]
txt = pathlib.Path(f).read_text()
bloco = pathlib.Path(canon).read_text().strip()
INI, FIM = "<!-- REGRA-9DRIVE:inicio", "<!-- REGRA-9DRIVE:fim -->"
estado = "substitui bloco existente" if (INI in txt and FIM in txt) else "acrescenta ao final"
print(f"  · {f}: {estado}")
PY
    continue
  fi
  [ -f "$f.bak-9drive" ] || cp "$f" "$f.bak-9drive"
  python3 - "$f" "$CANON" <<'PY'
import pathlib, sys
f, canon = sys.argv[1], sys.argv[2]
p = pathlib.Path(f)
txt = p.read_text()
bloco = pathlib.Path(canon).read_text().strip()
INI, FIM = "<!-- REGRA-9DRIVE:inicio", "<!-- REGRA-9DRIVE:fim -->"
if INI in txt and FIM in txt:
    a = txt.index(INI); b = txt.index(FIM) + len(FIM)
    p.write_text(txt[:a] + bloco + txt[b:])
else:
    p.write_text(txt.rstrip() + "\n\n" + bloco + "\n")
PY
  depois="$(md5sum < "$f")"
  if [ "$antes" = "$depois" ]; then
    echo "  · sem mudança: $f"; semmudanca=$((semmudanca + 1))
  elif grep -qF "REGRA-9DRIVE:inicio" "$f"; then
    if grep -qF "REGRA-9DRIVE" "$f.bak-9drive" 2>/dev/null; then
      echo "  · atualizado: $f"; instalados=$((instalados + 1))
    else
      echo "  · instalado: $f"; criados=$((criados + 1))
    fi
  fi
done

[ "$DRY" = 1 ] || echo "Pronto: $criados instalado(s), $instalados atualizado(s), $semmudanca sem mudança."
[ "$DRY" = 1 ] || echo "Backups dos originais: <arquivo>.bak-9drive"
