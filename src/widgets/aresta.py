import math
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsSimpleTextItem
from PyQt5.QtGui import QPen
from PyQt5.QtCore import Qt, QPointF

class Aresta(QGraphicsLineItem):
    def __init__(self, nodo1, nodo2):
        super().__init__()
        self.nodo1 = nodo1
        self.nodo2 = nodo2
        self.setPen(QPen(Qt.black, 2))

        self.texto = QGraphicsSimpleTextItem()
        self.texto.setZValue(1)

        self.atualizar()

        nodo1.arestas.append(self)
        nodo2.arestas.append(self)

    def atualizar(self):
        p1 = self.nodo1.pos()
        p2 = self.nodo2.pos()
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())

        distancia = math.hypot(p2.x() - p1.x(), p2.y() - p1.y())
        self.texto.setText(f"{distancia:.1f}")
        meio = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
        self.texto.setPos(meio)