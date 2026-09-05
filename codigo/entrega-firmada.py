"""Entrega de video con enlaces firmados que vencen — extracto de la plataforma.

Es la pieza que hace que un video pago no se pueda compartir con un enlace.
Tres ideas, en orden:

1. Los videos viven en un depósito privado (almacenamiento de objetos compatible
   con S3). No hay ninguna dirección pública fija a un video.
2. Cada pedido pasa primero por la plataforma, que decide si quien pide tiene
   derecho (está inscripta en ese curso). La misma regla vale para el video
   original y para cada lista de fragmentos del streaming adaptativo (HLS).
3. Si tiene derecho, recibe un enlace firmado que vence a las 6 horas. Para HLS,
   la lista de fragmentos se reescribe al vuelo: cada fragmento sale con su propia
   firma. Después, los fragmentos viajan del depósito al reproductor sin volver a
   pasar por el servidor web.

Extracto simplificado del código en producción. Falta lo que depende del resto de
la aplicación (modelos, sesión de la alumna), señalado en los comentarios.
"""
import boto3
from flask import abort, current_app, redirect

TTL_SEGUNDOS = 6 * 60 * 60          # cuánto vive cada enlace firmado
PREFIJO_HLS = "hls"                 # carpeta del depósito con los videos convertidos
EXT_VIDEO = (".mp4", ".mov", ".m4v", ".webm", ".mkv")


def _cliente():
    """Cliente S3 apuntando al depósito privado (credenciales por variables de entorno)."""
    c = current_app.config
    return boto3.client(
        "s3",
        endpoint_url=c["S3_ENDPOINT"],
        aws_access_key_id=c["S3_ACCESS_KEY"],
        aws_secret_access_key=c["S3_SECRET_KEY"],
        region_name=c.get("S3_REGION", "auto"),
    )


def _firmar(key):
    """Un enlace de descarga directa al depósito, válido solo por TTL_SEGUNDOS."""
    return _cliente().generate_presigned_url(
        "get_object",
        Params={"Bucket": current_app.config["S3_BUCKET"], "Key": key},
        ExpiresIn=TTL_SEGUNDOS,
    )


def _texto_del_deposito(key):
    obj = _cliente().get_object(Bucket=current_app.config["S3_BUCKET"], Key=key)
    return obj["Body"].read().decode("utf-8")


def video_original_de(rel):
    """Dado el pedido de una lista HLS, ¿de qué video original viene?

        curso/leccion-1/video-1/master.m3u8        → curso/leccion-1/video-1.mp4
        curso/leccion-1/video-1/1080p/index.m3u8   → curso/leccion-1/video-1.mp4

    Así la autorización es UNA sola regla: la del video original.
    """
    partes = rel.split("/")
    if partes[-1] == "master.m3u8":
        raiz = "/".join(partes[:-1])
    elif partes[-1] == "index.m3u8" and len(partes) >= 3:
        raiz = "/".join(partes[:-2])
    else:
        return None
    for ext in EXT_VIDEO:
        candidato = raiz + ext
        if existe_en_la_base(candidato):        # ← consulta a la base de videos (fuera del extracto)
            return candidato
    return None


def playlist_firmada(rel_hls):
    """Devuelve la lista .m3u8 lista para el reproductor.

    - `master.m3u8` (elige entre calidades) va tal cual: sus renglones son rutas
      relativas que vuelven a caer en esta misma vista, y se autorizan de nuevo.
    - `index.m3u8` (una calidad) se reescribe: cada fragmento pasa a ser un enlace
      firmado que vence.
    """
    key = f"{PREFIJO_HLS}/{rel_hls}"
    try:
        cuerpo = _texto_del_deposito(key)
    except Exception:
        return None                              # todavía no convertido → se usa el original
    if rel_hls.endswith("/master.m3u8"):
        return cuerpo
    carpeta = key.rsplit("/", 1)[0]
    salida = []
    for linea in cuerpo.splitlines():
        cruda = linea.strip()
        if cruda and not cruda.startswith("#"):  # cada renglón sin '#' es un fragmento
            linea = _firmar(f"{carpeta}/{cruda}")
        salida.append(linea)
    return "\n".join(salida) + "\n"


def entregar_medio(rel):
    """La vista que atiende /cursos/<ruta>. Acá se decide quién ve qué."""
    if ".." in rel.split("/"):                   # nadie sale del directorio
        abort(404)

    if rel.endswith(".m3u8"):
        original = video_original_de(rel)
        if original is None:
            abort(404)
        if not autorizado(original):             # ← ¿está inscripta en ese curso? (fuera del extracto)
            abort(403)
        cuerpo = playlist_firmada(rel)
        if cuerpo is None:
            abort(404)
        resp = current_app.response_class(cuerpo, mimetype="application/vnd.apple.mpegurl")
        resp.headers["Cache-Control"] = "private, max-age=60"
        return resp

    if not autorizado(rel):
        abort(403)
    return redirect(_firmar(rel), code=302)      # archivo suelto: enlace firmado que vence


# --- Fuera de este extracto (dependen del resto de la aplicación) -----------------
def existe_en_la_base(ruta):
    """¿Hay un video registrado con esa ruta? (consulta a la base)."""
    raise NotImplementedError


def autorizado(ruta):
    """¿La persona con sesión iniciada está inscripta en el curso de ese archivo?"""
    raise NotImplementedError
