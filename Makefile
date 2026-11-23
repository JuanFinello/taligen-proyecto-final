# Los comandos más usados. Todos corren desde la raíz del repo con el entorno de .venv.
# Si existe .env (ver .env.example), sus variables se cargan solas.
-include .env
export

PY := .venv/bin/python

.PHONY: ayuda instalar tests verificar interfaz chat evaluar todo

ayuda:  ## esta lista
	@grep -E '^[a-z]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

instalar:  ## crea .venv e instala las dependencias (con pytest)
	python3 -m venv .venv
	$(PY) -m pip install -r requirements-dev.txt

tests:  ## tests unitarios del código, sin modelo (~1 s, sin costo)
	$(PY) -m pytest

verificar:  ## controles de integridad de la base
	$(PY) analista/verificar_base.py

interfaz:  ## interfaz Streamlit en http://localhost:8501
	.venv/bin/streamlit run analista/interfaz.py

chat:  ## chat en la terminal («?» muestra de dónde sale cada número)
	$(PY) analista/puerta.py

evaluar:  ## evaluador: 21 casos contra lo esperado (~1 min, ~US$ 0,04)
	$(PY) evaluacion/evaluador.py

todo:  ## todo el enunciado: 20 preguntas, 5 conversaciones y 3 informes (~2 min, ~US$ 0,10)
	$(PY) evaluacion/correr_todo.py
