from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsSimpleTextItem
from PyQt5.QtCore import Qt

class Nodo(QGraphicsEllipseItem):
    def __init__(self, x, y, nome, raio=20):
        # Chama o construtor da classe base QGraphicsEllipseItem para criar a forma do nó.
        # Os parâmetros (-raio, -raio, 2 * raio, 2 * raio) definem um retângulo delimitador
        # para a elipse, centralizando-a em (0,0) em suas coordenadas locais.
        super().__init__(-raio, -raio, 2 * raio, 2 * raio)
        self.arestas = []  # Lista para armazenar as arestas conectadas a este nodo.
        self.nome = nome   # Nome (rótulo) do nodo.

        self.setBrush(Qt.green)  # Define a cor de preenchimento do nodo como verde.
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable)  # Permite que o nodo seja arrastado.
        # Permite que o item envie notificações de mudança de geometria (para que as arestas conectadas possam se atualizar).
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges)
        self.setPos(x, y)  # Define a posição inicial do nodo na cena.

        # Cria um QGraphicsSimpleTextItem para exibir o nome do nodo.
        # Ele é filho do nodo, então se move com ele.
        self.texto = QGraphicsSimpleTextItem(nome, self)
        self.texto.setPos(-5, -30)  # Posiciona o texto ligeiramente acima e à esquerda do centro do nodo.


    def itemChange(self, change, value):
        """
        Este método é chamado pelo framework Qt Graphics View quando uma propriedade
        do item (como a posição) está prestes a mudar ou já mudou.
        É usado para atualizar as arestas conectadas quando o nodo se move.
        """
        if change == QGraphicsEllipseItem.ItemPositionChange:
            # Se a posição do nodo está mudando, itera sobre todas as arestas
            # conectadas a este nodo e as atualiza.
            for aresta in self.arestas:
                aresta.atualizar() # Chama o método 'atualizar' da aresta para redesenhá-la.
        return super().itemChange(change, value) # Chama a implementação do método da classe base.