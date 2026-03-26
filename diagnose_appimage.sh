#!/bin/bash
echo "=== Diagnóstico do SpeedScan AppImage ==="
APPIMAGE="$1"

echo "1. Verificando arquivo:"
ls -lh "$APPIMAGE"
echo "Permissões: $(stat -c '%A %n' "$APPIMAGE")"

echo "2. Verificando se é executável:"
if [ -x "$APPIMAGE" ]; then
    echo "✅ Executável"
else
    echo "❌ Não executável - tentando corrigir..."
    chmod +x "$APPIMAGE"
fi

echo "3. Testando execução (5 segundos):"
timeout 5s "$APPIMAGE" --version 2>&1 || echo "Timeout ou erro esperado"

echo "4. Verificando dependências:"
ldd "$APPIMAGE" | grep "not found" || echo "✅ Sem dependências faltando"

echo "5. Verificando ambiente:"
echo "DISPLAY: $DISPLAY"
echo "XDG_RUNTIME_DIR: $XDG_RUNTIME_DIR"
echo "WAYLAND_DISPLAY: $WAYLAND_DISPLAY"

echo "=== Fim do diagnóstico ==="
