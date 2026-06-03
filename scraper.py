import re
import os
import pandas as pd

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from datetime import date
from sqlalchemy import create_engine, text
from ef_estados_financieros import entidades_ef
from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115 Safari/537.36"
    )
}

TARGET_TABLE  = os.getenv("DB_TABLE")
TARGET_SCHEMA = os.getenv("DB_SCHEMA")  

def build_engine():
    dialect  = os.getenv("DB_DIALECT")
    user     = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host     = os.getenv("DB_HOST")
    port     = os.getenv("DB_PORT")
    name     = os.getenv("DB_NAME")

    url = f"{dialect}://{user}:{password}@{host}:{port}/{name}"
    return create_engine(url, echo=False)

def build_session() -> Session:
    session = Session()
    session.headers.update(HEADERS)
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://",  HTTPAdapter(max_retries=retry))
    return session

def cargar_pagina(session: Session, url: str) -> BeautifulSoup | None:
    try:
        resp = session.get(url, timeout=60)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"[ERROR] {url}: {e}")
        return None

def procesar_tag_a(soup, nombre_entidad, url, keywords, avoid):
    resultados = []
    for enlace in soup.find_all("a", href=True):
        texto = enlace.get_text(separator=" ", strip=True).lower()
        if not texto:
            continue
        href = enlace["href"]
        contenido = re.sub(
            r"\s+", " ",
            f"{texto} {href.lower()}".replace("_", " ").replace("-", " "),
        )
        if any(p in contenido for p in avoid):
            continue
        if not all(k in contenido for k in keywords):
            continue
        resultados.append({
            "ENTIDAD":    nombre_entidad,
            "FUENTE_URL": url,
            "ETIQUETA":   "a",
            "TEXTO":      texto,
            "ENLACE":     href,
        })
    return resultados

def procesar_otros_tags(soup, nombre_entidad, tag, url, keywords, avoid):
    resultados = []
    for elem in soup.find_all(tag):
        texto = elem.get_text(separator=" ", strip=True).lower()
        if not texto or len(texto) < 5:
            continue
        if any(p in texto for p in avoid):
            continue
        if not all(k in texto for k in keywords):
            continue
        resultados.append({
            "ENTIDAD":    nombre_entidad,
            "FUENTE_URL": url,
            "ETIQUETA":   tag,
            "TEXTO":      texto,
            "ENLACE":     texto,
        })
    return resultados

def extraer_ano(row):
    if row["TEXTO"] == "SIN CONEXION / REGISTROS":
        return 0
    texto = str(row["TEXTO"])
    href  = str(row["ENLACE"])
    texto_limpio = texto.replace("–", "-").replace("_", " ").replace("-", " ")
    archivo = href.split("?")[0].split("/")[-1].lower()

    pattern = r"20\d{2}"

    def buscar(s):
        anos   = re.findall(pattern, s)
        validos = [a for a in anos if 2000 <= int(a) <= (date.today().year + 1)]
        return max(validos) if validos else None

    return (
        buscar(texto_limpio)
        or buscar(texto)
        or buscar(archivo)
        or buscar(href.split("?")[0])
    )

def ejecutar_scraping(entidades: dict, session: Session) -> pd.DataFrame:
    resultados = []

    for nombre_entidad, datos in entidades.items():
        print(f"[MENSAJE] Procesando {nombre_entidad}")
        resultados_entidad = []

        soup = cargar_pagina(session, datos["url"])

        if not soup:
            resultados.append({
                "ENTIDAD":    nombre_entidad,
                "FUENTE_URL": datos["url"],
                "ETIQUETA":   "ERROR_CONEXION",
                "TEXTO":      "SIN CONEXION / REGISTROS",
                "ENLACE":     "N/A",
            })
            continue

        keywords = [k.lower() for k in datos["keywords"]]
        avoid    = [a.lower() for a in datos["avoid"]]
        tags     = datos["tags"]

        for tag in tags:
            if tag == "a":
                resultados_entidad.extend(
                    procesar_tag_a(soup, nombre_entidad, datos["url"], keywords, avoid)
                )
            else:
                resultados_entidad.extend(
                    procesar_otros_tags(soup, nombre_entidad, tag, datos["url"], keywords, avoid)
                )

        if not resultados_entidad:
            resultados.append({
                "ENTIDAD":    nombre_entidad,
                "FUENTE_URL": datos["url"],
                "ETIQUETA":   "SIN_RESULTADOS",
                "TEXTO":      "SIN CONEXION / REGISTROS",
                "ENLACE":     "N/A",
            })
        else:
            resultados.extend(resultados_entidad)

    return pd.DataFrame(resultados)

def insertar_en_db(df: pd.DataFrame, engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("SELECT 1"))

    df.to_sql(
        name=TARGET_TABLE,
        con=engine,
        schema=TARGET_SCHEMA,
        if_exists="append",   
        index=False,
        chunksize=500,        
        method="multi",      
    )
    print(f"[MENSAJE] {len(df)} filas insertadas en '{TARGET_SCHEMA + '.' if TARGET_SCHEMA else ''}{TARGET_TABLE}'")

def main():
    session = build_session()

    df = ejecutar_scraping(entidades_ef, session)

    if df.empty:
        print("[AVISO] DataFrame vacio, no se insertó nada.")
        return

    df["ANO"] = df.apply(extraer_ano, axis=1)
    df["ANO"] = pd.to_numeric(df["ANO"], errors="coerce").fillna(0).astype(int)
    df = df.drop_duplicates()

    engine = build_engine()
    insertar_en_db(df, engine)

    errores = df[df["TEXTO"] == "SIN CONEXION / REGISTROS"]
    if not errores.empty:
        print("\n--- Entidades sin registros ---")
        print(errores[["ENTIDAD", "ANO"]])


if __name__ == "__main__":
    main()
