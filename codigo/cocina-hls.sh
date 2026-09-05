#!/bin/bash
# ---------------------------------------------------------------------------
# La cocina — deja un video en 3 calidades cortado en pedacitos (HLS).
#
#   cocina-hls.sh <academia> <clave-del-video>
#   ej: cocina-hls.sh artedehoy curso/videos/leccion-1/video-1.mp4
#
# VERSIÓN VPS (ING-09, casa = cero, 15/8/2026): corre en el VPS de Chile, lee el
# original del depósito de la academia en Cloudflare R2 y deja el HLS en el
# mismo depósito. Alias de mc por academia: r2-<academia>.
#
# Reglas de diseño:
#   · El original NO se toca. Lo cocinado va al lado, en hls/<ruta sin extension>/.
#   · Prioridad baja a proposito: la web SIEMPRE va primero.
#   · El master.m3u8 se sube ULTIMO: mientras no este, el aula usa el video original.
#     Asi nunca se sirve un video a medio cocinar.
# ---------------------------------------------------------------------------
set -euo pipefail

DEP="${1:?falta la academia (deposito)}"
KEY="${2:?falta la clave del video}"

ALIAS="r2-$DEP"                          # alias de mc de ESTA academia (su llave, su deposito)
RAIZ=/opt/druidatech-cocina
BASE="${KEY%.*}"                         # la ruta sin extension
T="$RAIZ/trabajo/$DEP/$BASE"             # area de trabajo (espeja la ruta)
DESTINO="$ALIAS/$DEP/hls/$BASE"

limpiar() { rm -rf "$T"; }
trap limpiar EXIT                        # no dejar basura ni aunque falle

mkdir -p "$T/salida/1080p" "$T/salida/720p" "$T/salida/480p"
mc cp -q "$ALIAS/$DEP/$KEY" "$T/fuente"

# 60 cuadros por segundo es el doble de lo que necesita una clase filmada con
# camara fija: se baja a 30 y ahi se va buena parte del sobrepeso.
#
# `-pix_fmt yuv420p` NO es un detalle: es el unico formato de color que
# reproducen todos los navegadores. Sin esto, con ciertos videos el codificador
# se planta y el video nunca se prepara.
nice -n 19 ionice -c3 ffmpeg -y -v error -i "$T/fuente" \
  -filter_complex "[0:v]fps=30,split=3[a][b][c];[a]scale=1920:-2[v0];[b]scale=1280:-2[v1];[c]scale=854:-2[v2]" \
  -map "[v0]" -map 0:a -map "[v1]" -map 0:a -map "[v2]" -map 0:a \
  -c:v libx264 -preset veryfast -profile:v high -pix_fmt yuv420p \
  -sc_threshold 0 -g 180 -keyint_min 180 \
  -b:v:0 4500k -maxrate:v:0 4800k -bufsize:v:0 9000k \
  -b:v:1 2500k -maxrate:v:1 2700k -bufsize:v:1 5000k \
  -b:v:2 1200k -maxrate:v:2 1300k -bufsize:v:2 2400k \
  -c:a aac -b:a 128k -ac 2 \
  -f hls -hls_time 6 -hls_playlist_type vod -hls_flags independent_segments \
  -hls_segment_filename "$T/salida/%v/seg_%05d.ts" \
  -master_pl_name master.m3u8 \
  -var_stream_map "v:0,a:0,name:1080p v:1,a:1,name:720p v:2,a:2,name:480p" \
  "$T/salida/%v/index.m3u8"

# Antes de subir la version nueva se vacia la carpeta destino: si el video fue
# reemplazado o una cocina anterior quedo a medias, los pedacitos viejos no
# pueden quedar mezclados con los nuevos (basura pagando deposito para siempre).
# La barra final importa: borra SOLO esta carpeta, no otra de nombre parecido.
mc rm --recursive --force "$DESTINO/" >/dev/null 2>&1 || true

for cal in 1080p 720p 480p; do
  mc cp -q --recursive "$T/salida/$cal/" "$DESTINO/$cal/"
done
mc cp -q "$T/salida/master.m3u8" "$DESTINO/master.m3u8"

echo "OK cocinado: $DEP/$KEY"
