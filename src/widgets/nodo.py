from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsSimpleTextItem
from PyQt5.QtCore import Qt

class Nodo(QGraphicsEllipseItem):
    def __init__(self, x, y, nome, raio=20):
        super().__init__(-raio, -raio, 2 * raio, 2 * raio)
        self.arestas = []
        self.nome = nome

        self.setBrush(Qt.green)
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable)
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges)
        self.setPos(x, y)

        self.texto = QGraphicsSimpleTextItem(nome, self)
        self.texto.setPos(-5, -30)


    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.ItemPositionChange:
            for aresta in self.arestas:
                aresta.atualizar()
        return super().itemChange(change, value)