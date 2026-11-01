"""Clasifica solo el texto que sobrevivió al filtro."""

from __future__ import annotations

import json
import urllib.request
from collections import defaultdict

from orquestador.config import Ajustes
from orquestador.modelos import ETIQUETAS, MODULOS, SENTIMIENTOS, Hallazgo, Respuesta

TOPE_USD = 3.0


def clasificar(respuestas: list[Respuesta], ajustes: Ajustes, mes: str) -> tuple[list[Hallazgo], float, bool]:
    grupos = _grupos_exactos(respuestas)
    costo = 0.0
    corte = False
    if ajustes.tiene_embeddings and len(grupos) > 1:
        unidos, tokens = _unir_parecidos(grupos, ajustes)
        if unidos is not None:
            costo += tokens / 1_000_000 * ajustes.usd_por_millon
            grupos = unidos
            if costo >= TOPE_USD:
                corte = True
    hallazgos: list[Hallazgo] = []
    for firma in sorted(grupos):
        filas = sorted(grupos[firma], key=lambda item: item.id)
        if not ajustes.tiene_modelo or corte or costo >= TOPE_USD:
            if ajustes.tiene_modelo and costo >= TOPE_USD:
                corte = True
            motivo = (
                "El costo estimado llegó a 3 USD antes de clasificar todas las quejas."
                if corte
                else "Sin modelo configurado; el caso queda en revisión humana."
            )
            hallazgos.append(_revision(filas, mes, motivo))
            continue
        resultado, tokens = _consultar(ajustes, _representante(filas))
        costo += tokens / 1_000_000 * ajustes.usd_por_millon
        if costo >= TOPE_USD:
            corte = True
        hallazgo = _desde_modelo(filas, mes, resultado)
        if corte and hallazgo.estado != "requiere_revision":
            hallazgo = _revision(filas, mes, "El costo estimado llegó a 3 USD antes de clasificar todas las quejas.")
        hallazgos.append(hallazgo)
    total = sum(item.conteo for item in hallazgos)
    for hallazgo in hallazgos:
        color, porcentaje = color_por_conteo(hallazgo.conteo, total)
        hallazgo.criticidad = color
        hallazgo.porcentaje = porcentaje
    return hallazgos, round(costo, 6), corte


def color_por_conteo(conteo: int, total: int) -> tuple[str, float]:
    porcentaje = round(conteo * 100 / total, 2)
    if porcentaje <= 20:
        color = "verde"
    elif porcentaje <= 50:
        color = "amarillo"
    else:
        color = "rojo"
    return color, porcentaje


def _grupos_exactos(respuestas: list[Respuesta]) -> dict[str, list[Respuesta]]:
    grupos: dict[str, list[Respuesta]] = defaultdict(list)
    for respuesta in respuestas:
        if respuesta.es_ruido or respuesta.es_b2c or respuesta.fuera_de_mes:
            continue
        if not respuesta.pregunta_anonimizada.strip():
            continue
        grupos[_firma(respuesta.pregunta_anonimizada)].append(respuesta)
    return grupos


def _unir_parecidos(
    grupos: dict[str, list[Respuesta]], ajustes: Ajustes
) -> tuple[dict[str, list[Respuesta]] | None, int]:
    firmas = sorted(grupos)
    textos = [_representante(grupos[firma]) for firma in firmas]
    vectores, tokens = _embeddings(ajustes, textos)
    if vectores is None or len(vectores) != len(firmas):
        return None, 0
    padre = list(range(len(firmas)))

    def raiz(indice: int) -> int:
        while padre[indice] != indice:
            padre[indice] = padre[padre[indice]]
            indice = padre[indice]
        return indice

    pares = []
    for i in range(len(firmas)):
        for j in range(i + 1, len(firmas)):
            similitud = _coseno(vectores[i], vectores[j])
            if similitud >= ajustes.embedding_umbral:
                pares.append((similitud, i, j))
    for _, i, j in sorted(pares, reverse=True):
        izquierda, derecha = raiz(i), raiz(j)
        if izquierda != derecha:
            padre[derecha] = izquierda
    unidos: dict[str, list[Respuesta]] = {}
    for indice, firma in enumerate(firmas):
        unidos.setdefault(firmas[raiz(indice)], []).extend(grupos[firma])
    return unidos, tokens


def _embeddings(ajustes: Ajustes, textos: list[str]) -> tuple[list[list[float]] | None, int]:
    cuerpo = {"model": ajustes.embedding_name, "input": textos}
    solicitud = urllib.request.Request(
        f"{ajustes.model_base_url}/embeddings",
        data=json.dumps(cuerpo).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {ajustes.model_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(solicitud, timeout=60) as respuesta:
            payload = json.loads(respuesta.read().decode("utf-8"))
        datos = sorted(payload.get("data") or [], key=lambda item: item.get("index", 0))
        vectores = [item.get("embedding") for item in datos]
        if len(vectores) != len(textos) or any(not isinstance(vector, list) or not vector for vector in vectores):
            return None, 0
        tokens = int((payload.get("usage") or {}).get("total_tokens") or 0)
        return vectores, tokens
    except Exception:
        return None, 0


def _coseno(izquierda: list[float], derecha: list[float]) -> float:
    if len(izquierda) != len(derecha) or not izquierda:
        return 0.0
    producto = sum(a * b for a, b in zip(izquierda, derecha))
    norma_izquierda = sum(a * a for a in izquierda) ** 0.5
    norma_derecha = sum(b * b for b in derecha) ** 0.5
    if norma_izquierda == 0 or norma_derecha == 0:
        return 0.0
    return producto / (norma_izquierda * norma_derecha)


def _firma(texto: str) -> str:
    return " ".join(texto.lower().split())


def _representante(filas: list[Respuesta]) -> str:
    orden = sorted(filas, key=lambda item: item.id)
    conteos: dict[str, int] = {}
    for fila in orden:
        conteos[fila.pregunta_anonimizada] = conteos.get(fila.pregunta_anonimizada, 0) + 1
    elegido = orden[0].pregunta_anonimizada
    for fila in orden:
        if conteos[fila.pregunta_anonimizada] > conteos[elegido]:
            elegido = fila.pregunta_anonimizada
    return elegido


def _comentarios(filas: list[Respuesta]) -> list[str]:
    return [fila.pregunta_anonimizada for fila in sorted(filas, key=lambda item: item.id)]


def _revision(filas: list[Respuesta], mes: str, motivo: str) -> Hallazgo:
    orden = sorted(filas, key=lambda item: item.id)
    return Hallazgo(
        id=f"hallazgo-{orden[0].id}",
        mes=mes,
        conteo=len(orden),
        confianza=0,
        estado="requiere_revision",
        respuestas=[fila.id for fila in orden],
        pestanas=sorted({fila.pestana for fila in orden}),
        motivo=motivo,
        comentario=_representante(orden),
        comentarios=_comentarios(orden),
    )


def _desde_modelo(filas: list[Respuesta], mes: str, resultado: dict | None) -> Hallazgo:
    base = _revision(filas, mes, "La confianza es menor a 70 o la taxonomía no es válida.")
    if not resultado:
        return base
    modulo = resultado.get("modulo")
    etiqueta = resultado.get("etiqueta")
    sentimiento = resultado.get("sentimiento")
    try:
        confianza = int(resultado.get("confianza"))
        intensidad = int(resultado.get("intensidad", 0))
    except (TypeError, ValueError):
        return base
    sintesis = str(resultado.get("sintesis") or "").strip()
    lineas = [linea for linea in sintesis.splitlines() if linea.strip()][:2]
    if (
        confianza < 70
        or modulo not in MODULOS
        or etiqueta not in ETIQUETAS
        or sentimiento not in SENTIMIENTOS
        or not 0 <= intensidad <= 100
        or not lineas
    ):
        return base
    return Hallazgo(
        id=base.id,
        mes=mes,
        modulo=modulo,
        etiqueta=etiqueta,
        sintesis="\n".join(lineas),
        conteo=len(filas),
        confianza=confianza,
        sentimiento=sentimiento,
        intensidad=intensidad,
        estado="clasificado",
        respuestas=base.respuestas,
        pestanas=base.pestanas,
        motivo=str(resultado.get("justificacion") or "Clasificado con la taxonomía oficial."),
        comentario=base.comentario,
    )


def _consultar(ajustes: Ajustes, texto: str) -> tuple[dict | None, int]:
    cuerpo = {
        "model": ajustes.model_name,
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Responde solo JSON con las claves modulo, etiqueta, "
                    "sintesis, sentimiento, intensidad, confianza y justificacion. "
                    f"modulo es uno de {list(MODULOS)}. etiqueta es uno de {list(ETIQUETAS)}. "
                    "sentimiento es positivo, neutral o negativo. "
                    "confianza e intensidad son enteros de 0 a 100. sintesis tiene como máximo dos líneas. "
                    "No inventes hechos que no estén en el comentario."
                ),
            },
            {"role": "user", "content": texto},
        ],
    }
    solicitud = urllib.request.Request(
        f"{ajustes.model_base_url}/chat/completions",
        data=json.dumps(cuerpo).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {ajustes.model_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(solicitud, timeout=60) as respuesta:
            payload = json.loads(respuesta.read().decode("utf-8"))
        contenido = payload["choices"][0]["message"]["content"]
        tokens = int((payload.get("usage") or {}).get("total_tokens") or 500)
        return _json_de_texto(contenido), tokens
    except Exception:
        return None, 500


def _json_de_texto(contenido: str) -> dict | None:
    inicio = contenido.find("{")
    fin = contenido.rfind("}")
    if inicio < 0 or fin <= inicio:
        return None
    try:
        valor = json.loads(contenido[inicio : fin + 1])
    except json.JSONDecodeError:
        return None
    return valor if isinstance(valor, dict) else None
