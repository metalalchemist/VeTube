"""Utilidades compartidas por las pruebas del firmador local de TikTok.

Las tramas se fabrican con el mismo protobuf que usa la librería
(TikTokLive.proto), así que ninguna prueba necesita tocar la red de TikTok ni
guardar capturas reales, que llevarían firma dentro.
"""

import base64
import gzip

from TikTokLive.proto import (
    ProtoMessageFetchResult,
    ProtoMessageFetchResultBaseProtoMessage,
    PushHeader,
    WebcastPushFrame,
)


def respuesta_con_mensajes(*metodos, cursor="1789072724354_0_1_1_0_0", need_ack=True):
    """El ProtoMessageFetchResult que va dentro de una trama 'msg'."""
    return ProtoMessageFetchResult(
        messages=[
            ProtoMessageFetchResultBaseProtoMessage(
                method=metodo,
                payload=b"",
                msg_id=i + 1,
                msg_type=1,
                offset=0,
                is_history=False,
            )
            for i, metodo in enumerate(metodos)
        ],
        cursor=cursor,
        need_ack=need_ack,
        internal_ext="ext",
    )


def trama(payload, *, payload_type="msg", compress_type="none", log_id=1, seq_id=1):
    """Una trama binaria como las que el navegador recibe del webcast.

    compress_type acepta 'none' y 'gzip' porque en un directo real llegan las
    dos; None deja la trama sin la cabecera, que también pasa.
    """
    cabeceras = [PushHeader(key="im_cursor", value="c"), PushHeader(key="server_time", value="0")]
    if compress_type is not None:
        cabeceras.insert(0, PushHeader(key="compress_type", value=compress_type))
    if compress_type == "gzip":
        payload = gzip.compress(payload)
    return bytes(
        WebcastPushFrame(
            payload_type=payload_type,
            payload_encoding="pb",
            payload=payload,
            headers=cabeceras,
            log_id=log_id,
            seq_id=seq_id,
        )
    )


def trama_msg(*metodos, compress_type="none", **kwargs):
    """Trama 'msg' con los eventos indicados (sin ninguno, si no se pasa nada)."""
    return trama(
        bytes(respuesta_con_mensajes(*metodos, **kwargs)), compress_type=compress_type
    )


def trama_hb():
    """El latido que manda el servidor: transporte, sin eventos dentro."""
    return trama(b"", payload_type="hb")


def en_base64(datos):
    return base64.b64encode(datos).decode("ascii")
