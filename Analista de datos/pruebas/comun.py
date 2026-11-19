"""Lo que comparten las simulaciones de datos (decisiones 87 y 88): el ruido, el redondeo y la carga por CSV."""
import csv
import math

RUIDO = 0.15
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]


def ruido(rng, sigma=RUIDO):
    """Lognormal con media 1 (μ = −σ²/2): con μ = 0 la media sería e^(σ²/2) ≈ 1,011 y agregaría un crecimiento falso."""
    return rng.lognormvariate(-sigma ** 2 / 2, sigma)


def redondeo_estocastico(x, rng):
    """Redondea hacia arriba con probabilidad igual a la parte decimal: en promedio conserva el valor. Con 1 o 2
    unidades por fila, redondear siempre borraría cualquier cambio chico."""
    piso = math.floor(x)
    return piso + (rng.random() < x - piso)


def cargar(con, tabla, filas, carpeta):
    """Inserta filas en una tabla pasando por un CSV (mucho más rápido que fila por fila)."""
    ruta = carpeta / f"_{tabla}.csv"
    with open(ruta, "w", newline="") as f:
        escritor = csv.writer(f)
        tipos = {c: t for c, t, *_ in con.execute(f"DESCRIBE {tabla}").fetchall()}
        escritor.writerow(list(tipos))
        escritor.writerows(filas)
    con.execute(f"INSERT INTO {tabla} SELECT * FROM read_csv(?, header = true, columns = ?)", [str(ruta), tipos])
    ruta.unlink()
