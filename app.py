from flask import Flask, request, jsonify, send_file
import matplotlib.pyplot as plt
import networkx as nx
import io
import base64
import os

app = Flask(__name__)

class Actividad:
    def __init__(self, nombre, duracion, predecesoras):
        self.nombre = nombre
        self.duracion = duracion
        self.predecesoras = predecesoras
        self.inicio_temprano = 0
        self.final_temprano = 0
        self.inicio_tardio = 0
        self.final_tardio = 0
        self.holgura = 0

@app.route('/ruta-critica', methods=['POST'])
def calcular():
    datos = request.json['actividades']
    actividades = [Actividad(a['nombre'], a['duracion'], a['predecesoras']) for a in datos]

    G = nx.DiGraph()
    nodos = {a.nombre: a for a in actividades}

    for act in actividades:
        G.add_node(act.nombre, dur=act.duracion)
        for pre in act.predecesoras:
            if pre not in nodos:
                return jsonify({"error": f"Predecesora '{pre}' no encontrada"}), 400
            G.add_edge(pre, act.nombre)

    for nodo in nx.topological_sort(G):
        act = nodos[nodo]
        act.inicio_temprano = max(nodos[pre].final_temprano for pre in act.predecesoras) if act.predecesoras else 0
        act.final_temprano = act.inicio_temprano + act.duracion

    fin_proyecto = max(a.final_temprano for a in actividades)

    for nodo in reversed(list(nx.topological_sort(G))):
        act = nodos[nodo]
        act.final_tardio = min(nodos[succ].inicio_tardio for succ in G.successors(nodo)) if list(G.successors(nodo)) else fin_proyecto
        act.inicio_tardio = act.final_tardio - act.duracion
        act.holgura = act.inicio_tardio - act.inicio_temprano

    ruta_critica = [a.nombre for a in actividades if a.holgura == 0]

    pos = nx.spring_layout(G)
    colores = ['red' if nodo in ruta_critica else 'skyblue' for nodo in G.nodes()]
    labels = {n: f"{n}\nT:{nodos[n].duracion}\nH:{nodos[n].holgura}" for n in G.nodes()}

    plt.figure(figsize=(10, 6))
    nx.draw(G, pos, with_labels=True, labels=labels, node_color=colores, node_size=2500, font_size=10)
    nx.draw_networkx_edges(G, pos, arrows=True)
    plt.title("Red de Actividades (Ruta Crítica en Rojo)")
    plt.axis('off')

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    imagen_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    resultados = [{
        'nombre': a.nombre,
        'inicio_temprano': a.inicio_temprano,
        'final_temprano': a.final_temprano,
        'inicio_tardio': a.inicio_tardio,
        'final_tardio': a.final_tardio,
        'holgura': a.holgura
    } for a in actividades]

    return jsonify({
        'ruta_critica': ruta_critica,
        'duracion_total': fin_proyecto,
        'actividades': resultados,
        'imagen': imagen_base64
    })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)