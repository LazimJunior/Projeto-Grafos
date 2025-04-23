from PyQt5.QtWidgets import QMainWindow, QGraphicsView, QGraphicsScene
from widgets.nodo import Nodo
from widgets.aresta import Aresta

class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grafo Interativo")
        self.setGeometry(100, 100, 800, 600)

        self.view = QGraphicsView(self)
        self.setCentralWidget(self.view)
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)

        self.nodos = []
        self.arestas = []

        self.criar_grafo()

    def criar_grafo(self):
        posicoes = [(100, 100), (300, 100), (300, 300), (100, 300)]
        nomes = ['A', 'B', 'C', 'D']

        for nome, (x, y) in zip(nomes, posicoes):
            nodo = Nodo(x, y, nome)
            self.scene.addItem(nodo)
            self.nodos.append(nodo)

        conexoes = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]
        for i, j in conexoes:
            aresta = Aresta(self.nodos[i], self.nodos[j])
            self.scene.addItem(aresta)
            self.scene.addItem(aresta.texto)
            self.arestas.append(aresta)