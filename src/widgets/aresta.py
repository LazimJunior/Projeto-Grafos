import math
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsSimpleTextItem
from PyQt5.QtGui import QPen
from PyQt5.QtCore import Qt, QPointF


class Aresta(QGraphicsLineItem):
    def __init__(self, nodo1, nodo2):
        super().__init__()
        self.nodo1 = nodo1  # Referência ao primeiro nodo da aresta.
        self.nodo2 = nodo2  # Referência ao segundo nodo da aresta.
        self.setPen(QPen(Qt.black, 2))  # Define a caneta para desenhar a linha da aresta (cor preta, espessura 2).

        self.texto = QGraphicsSimpleTextItem()  # Cria um item de texto para exibir informações sobre a aresta.
        self.texto.setZValue(1)  # Define um Z-Value maior para o texto aparecer sobre a linha da aresta.

        self.atualizar()  # Chama o método para posicionar e atualizar a aresta e seu texto.

        # Adiciona a aresta à lista de arestas de cada nodo conectado.
        nodo1.arestas.append(self)
        nodo2.arestas.append(self)

    def atualizar(self):
        """
        Atualiza a geometria da aresta e a posição do seu texto.
        É chamado quando os nodos conectados se movem.
        """
        p1 = self.nodo1.pos()  # Posição do primeiro nodo.
        p2 = self.nodo2.pos()  # Posição do segundo nodo.
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())  # Define a linha da aresta entre os centros dos nodos.

        distancia = math.hypot(p2.x() - p1.x(), p2.y() - p1.y())  # Calcula a distância entre os nodos.
        self.texto.setText(f"{distancia:.1f}")  # Define o texto da aresta como a distância formatada.

        # Calcula o ponto médio da linha para posicionar o texto.
        meio = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
        self.texto.setPos(meio)  # Define a posição do texto.