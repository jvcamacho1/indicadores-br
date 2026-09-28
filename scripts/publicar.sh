#!/usr/bin/env bash
# Publica uma pasta na branch gh-pages do mesmo repositório.
#
# A branch guarda só o site da última publicação (commit órfão, push
# forçado): o histórico que importa é o do código, na main.
set -euo pipefail

SITE_DIR="${1:-build/site}"
REMOTE_URL="${PUBLICAR_REMOTE:-$(git remote get-url origin)}"

if [[ ! -f "$SITE_DIR/index.html" || ! -f "$SITE_DIR/data.json" ]]; then
  echo "erro: $SITE_DIR não tem index.html e data.json. Rode 'make site' antes." >&2
  exit 1
fi
if grep -q '"sintetico": true' "$SITE_DIR/data.json" && [[ "${PERMITIR_SINTETICO:-}" != "1" ]]; then
  echo "erro: o site foi montado com dados sintéticos. Não publico isso (PERMITIR_SINTETICO=1 força)." >&2
  exit 1
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cp -r "$SITE_DIR"/. "$tmp"/
touch "$tmp/.nojekyll"
git -C "$tmp" init -q -b gh-pages
git -C "$tmp" add -A
git -C "$tmp" -c user.name="${GIT_AUTHOR_NAME:-indicadores-br}" -c user.email="${GIT_AUTHOR_EMAIL:-indicadores-br@users.noreply.github.com}" \
  commit -q -m "Publica o painel ($(date -u +%Y-%m-%dT%H:%MZ))"
git -C "$tmp" push -q -f "$REMOTE_URL" gh-pages
echo "publicado em gh-pages"
