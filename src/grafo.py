import networkx as nx
import random
from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsEllipseItem, QGraphicsLineItem,
    QGraphicsTextItem, QGraphicsScene, QGraphicsDropShadowEffect,
    QMessageBox, QInputDialog
)
from PyQt5.QtGui import QPen, QColor, QFont, QPainter, QBrush, QPolygonF
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QRectF
from math import cos, sin, atan2, pi

# =================================================================================
#  ITENS GRÁFICOS (NÓS E ARESTAS)
# =================================================================================

class NodeItem(QGraphicsEllipseItem):
    """Representa um nó (vértice) que pode ser arrastado na cena."""

    def __init__(self, label, x, y, radius=20):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.edges = []
        self.radius = radius
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable)
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges)

        self.normal_brush = QBrush(QColor("#5E81AC"))
        self.selected_brush = QBrush(QColor("#88C0D0"))

        self.setBrush(self.normal_brush)
        self.setPen(QPen(QColor("#88C0D0"), 2))

        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor("#88C0D0"))
        self.shadow.setOffset(0, 0)
        self.shadow.setEnabled(False)
        self.setGraphicsEffect(self.shadow)

        self.text_item = QGraphicsTextItem(label, self)
        font = QFont("Segoe UI", 11, QFont.Bold)
        self.text_item.setFont(font)
        self.text_item.setDefaultTextColor(QColor("#ECEFF4"))
        self.text_item.setPos(-self.text_item.boundingRect().width() / 2,
                              -self.text_item.boundingRect().height() / 2)

        self.setPos(x, y)
        self.label = label

    def add_edge(self, edge):
        self.edges.append(edge)

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_position()
        return super().itemChange(change, value)

    def set_selected(self, is_selected):
        self.shadow.setEnabled(is_selected)
        self.setBrush(self.selected_brush if is_selected else self.normal_brush)

class EdgeItem(QGraphicsLineItem):
    """Representa uma aresta entre dois nós, com capacidade de desenhar setas."""

    def __init__(self, source_node: NodeItem, dest_node: NodeItem, weight: int = 1, is_directed=False):
        super().__init__()
        self.source_node = source_node
        self.dest_node = dest_node
        self.peso = weight
        self.is_directed = is_directed
        self.arrow_size = 15

        self.setZValue(-1)  # Coloca a aresta atrás dos nós
        self.line_pen = QPen(QColor("#4C566A"), 2.5)
        self.setPen(self.line_pen)

        self.text_item_edge = QGraphicsTextItem(str(self.peso))
        font = QFont("Segoe UI", 10)
        self.text_item_edge.setFont(font)
        self.text_item_edge.setDefaultTextColor(QColor("#D8DEE9"))

        self.source_node.add_edge(self)
        self.dest_node.add_edge(self)
        self.update_position()

    def add_text_to_scene(self, scene):
        scene.addItem(self.text_item_edge)

    def set_weight(self, weight):
        self.peso = weight
        self.text_item_edge.setPlainText(str(self.peso))

    def update_position(self):
        self.prepareGeometryChange()
        self.update()

        # Atualiza a posição do texto
        p1 = self.source_node.pos()
        p2 = self.dest_node.pos()
        mid_x = (p1.x() + p2.x()) / 2
        mid_y = (p1.y() + p2.y()) / 2
        self.text_item_edge.setPos(mid_x, mid_y)

    def boundingRect(self):
        extra = (self.pen().width() + self.arrow_size) / 2.0
        p1 = self.source_node.pos()
        p2 = self.dest_node.pos()
        return QRectF(p1, p2).normalized().adjusted(-extra, -extra, extra, extra)

    def paint(self, painter, option, widget=None):
        # Pega a posição central dos nós
        source_center = self.source_node.pos()
        dest_center = self.dest_node.pos()

        # Calcula o ângulo da linha
        angle = atan2(dest_center.y() - source_center.y(), dest_center.x() - source_center.x())

        # Calcula os pontos de intersecção da linha com a borda dos nós
        source_radius = self.source_node.radius
        dest_radius = self.dest_node.radius

        source_point = source_center + QPointF(cos(angle) * source_radius, sin(angle) * source_radius)
        dest_point = dest_center - QPointF(cos(angle) * dest_radius, sin(angle) * dest_radius)

        # Define a linha a ser desenhada
        self.setLine(QPointF(source_point).x(), QPointF(source_point).y(), QPointF(dest_point).x(),
                     QPointF(dest_point).y())

        # Desenha a linha principal
        painter.setPen(self.line_pen)
        painter.drawLine(self.line())

        # Se for orientado, desenha a seta
        if self.is_directed:
            # Calcula os pontos da seta
            arrow_p1 = dest_point + QPointF(sin(angle + pi / 3) * self.arrow_size,
                                            cos(angle + pi / 3) * self.arrow_size)
            arrow_p2 = dest_point + QPointF(sin(angle + pi - pi / 3) * self.arrow_size,
                                            cos(angle + pi - pi / 3) * self.arrow_size)

            arrow_head = QPolygonF()
            arrow_head.clear()
            arrow_head.append(dest_point)
            arrow_head.append(arrow_p1)
            arrow_head.append(arrow_p2)

            painter.setBrush(QBrush(QColor("#4C566A")))
            painter.drawPolygon(arrow_head)

class GraphView(QGraphicsView):
    """A área de visualização principal que controla o GraphicsView."""
    graphChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.nodes = {}
        self.edges = []
        self.is_directed = False

        self.setBackgroundBrush(QBrush(QColor("#262b33")))
        self.selected_node = None
        self.edit_weights_mode = False

    def set_graph_type(self, is_directed: bool):
        """Define o tipo do grafo (orientado ou não)."""
        self.is_directed = is_directed

    def set_edit_weights_mode(self, enabled: bool):
        """Ativa ou desativa o modo de edição de pesos."""
        self.edit_weights_mode = enabled

    def add_node(self, label, x, y):
        if label in self.nodes: return
        node = NodeItem(label, x, y)
        self.nodes[label] = node
        self.scene.addItem(node)

    def add_edge(self, label1, label2, weight: int = 1):
        if label1 not in self.nodes or label2 not in self.nodes: return
        node1 = self.nodes[label1]
        node2 = self.nodes[label2]

        for edge in self.edges:
            if (edge.source_node == node1 and edge.dest_node == node2) or \
                    (not self.is_directed and edge.source_node == node2 and edge.dest_node == node1):
                return

        edge = EdgeItem(node1, node2, weight, self.is_directed)
        self.edges.append(edge)
        self.scene.addItem(edge)
        edge.add_text_to_scene(self.scene)

    def clear(self):
        self.scene.clear()
        self.nodes = {}
        self.edges = []
        self.selected_node = None

    def generate_adjacency_matrix(self):
        labels = sorted(self.nodes.keys())
        size = len(labels)
        index_map = {label: i for i, label in enumerate(labels)}
        mat = [[0] * size for _ in range(size)]

        for edge in self.edges:
            try:
                i = index_map[edge.source_node.label]
                j = index_map[edge.dest_node.label]
                mat[i][j] = edge.peso
                if not self.is_directed:
                    mat[j][i] = edge.peso
            except KeyError:
                print(f"Aviso: Chave não encontrada ao gerar matriz para aresta.")
                continue
        return labels, mat

    def update_from_matrix(self, labels, matrix):
        self.clear()
        n = len(labels)
        if n == 0: return

        center_x, center_y = self.width() / 2, self.height() / 2
        radius = min(center_x, center_y) * 0.7 if center_x > 0 else 100

        for i, label in enumerate(labels):
            angle = 2 * 3.1415926535 * i / n
            x = center_x + cos(angle) * radius
            y = center_y + sin(angle) * radius
            self.add_node(label, x, y)

        for i in range(n):
            for j in range(n if self.is_directed else i, n):
                weight = matrix[i][j]
                if weight > 0:
                    self.add_edge(labels[i], labels[j], weight)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            item_at = self.itemAt(event.pos())

            if self.edit_weights_mode:
                clicked_edge = None
                if isinstance(item_at, QGraphicsTextItem):
                    for edge in self.edges:
                        if edge.text_item_edge == item_at:
                            clicked_edge = edge
                            break
                if clicked_edge:
                    self.edit_edge_weight(clicked_edge)
                    return

            scene_pos = self.mapToScene(event.pos())
            current_node_item = None
            if isinstance(item_at, NodeItem):
                current_node_item = item_at
            elif isinstance(item_at, QGraphicsTextItem) and isinstance(item_at.parentItem(), NodeItem):
                current_node_item = item_at.parentItem()

            if current_node_item:
                if self.selected_node is None:
                    self.selected_node = current_node_item
                    self.selected_node.set_selected(True)
                    if self.window() and hasattr(self.window(), 'statusBar'):
                        self.window().statusBar().showMessage(f"Nó '{self.selected_node.label}' selecionado.")
                else:
                    if current_node_item != self.selected_node:
                        # --- INÍCIO DA MUDANÇA: LÓGICA PARA CRIAR ARESTA ---
                        new_weight, ok = QInputDialog.getInt(self, "Peso da Aresta",
                                                             "Digite o peso para a nova aresta:", 1, 1, 999, 1)

                        if ok:  # Se o usuário não clicou em "Cancelar"
                            weight_exists = any(edge.peso == new_weight for edge in self.edges)
                            proceed = True

                            if weight_exists:
                                reply = QMessageBox.question(self, 'Confirmar Peso Duplicado',
                                                             f'O peso "{new_weight}" já existe em outra aresta. Deseja continuar?',
                                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                if reply == QMessageBox.No:
                                    proceed = False

                            if proceed:
                                self.add_edge(self.selected_node.label, current_node_item.label, new_weight)
                                self.graphChanged.emit()
                        # --- FIM DA MUDANÇA ---

                    self.selected_node.set_selected(False)
                    self.selected_node = None
                    if self.window() and hasattr(self.window(), 'statusBar'):
                        self.window().statusBar().showMessage("Pronto.")
            else:
                if self.selected_node:
                    self.selected_node.set_selected(False)
                    self.selected_node = None
                    if self.window() and hasattr(self.window(), 'statusBar'):
                        self.window().statusBar().showMessage("Pronto.")
                else:
                    if len(self.nodes) >= 26:
                        QMessageBox.information(self, "Limite Atingido",
                                                "Não é possível adicionar mais nós (limite A-Z).")
                        return

                    label = None
                    for i in range(26):
                        potential_label = chr(ord('A') + i)
                        if potential_label not in self.nodes:
                            label = potential_label
                            break

                    if label:
                        self.add_node(label, scene_pos.x(), scene_pos.y())
                        if self.window() and hasattr(self.window(), 'statusBar'):
                            self.window().statusBar().showMessage(f"Nó '{label}' criado.", 3000)

        super().mousePressEvent(event)

    def edit_edge_weight(self, edge):
        # --- INÍCIO DA MUDANÇA: LÓGICA PARA EDITAR ARESTA ---
        current_weight = edge.peso
        new_weight, ok = QInputDialog.getInt(self, "Alterar Peso da Aresta",
                                             f"Novo peso para a aresta ({edge.source_node.label} ↔ {edge.dest_node.label}):",
                                             current_weight, 1, 999, 1)

        if ok and new_weight != current_weight:
            # Verifica se o peso já existe em outra aresta
            weight_exists = any(other.peso == new_weight for other in self.edges if other is not edge)
            proceed = True

            if weight_exists:
                reply = QMessageBox.question(self, 'Confirmar Peso Duplicado',
                                             f'O peso "{new_weight}" já existe em outra aresta. Deseja continuar?',
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    proceed = False

            if proceed:
                edge.set_weight(new_weight)
                self.graphChanged.emit()
                if self.window() and hasattr(self.window(), 'statusBar'):
                    self.window().statusBar().showMessage(f"Peso da aresta alterado para {new_weight}.", 4000)
        # --- FIM DA MUDANÇA ---

    def generate_random_nodes(self, n_nodes):
        self.clear()
        labels = [chr(ord('A') + i) for i in range(n_nodes)]

        center_x, center_y = self.width() / 2, self.height() / 2
        radius = min(center_x, center_y) * 0.7 if center_x > 0 and center_y > 0 else 100

        for i, label in enumerate(labels):
            if n_nodes == 0: break
            angle = 2 * 3.1415926535 * i / n_nodes
            x = center_x + radius * cos(angle)
            y = center_y + radius * sin(angle)
            self.add_node(label, x, y)

        max_edges = min(n_nodes * (n_nodes - 1) // 2, n_nodes + random.randint(0, n_nodes // 2))

        node_keys = list(self.nodes.keys())
        if len(node_keys) < 2: return

        # Garante que os pesos aleatórios sejam únicos para não acionar o diálogo de confirmação
        existing_weights = set()
        while len(self.edges) < max_edges:
            n1_label, n2_label = random.sample(node_keys, 2)
            edge_exists = any((e.source_node.label == n1_label and e.dest_node.label == n2_label) or \
                              (e.source_node.label == n2_label and e.dest_node.label == n1_label) for e in self.edges)
            if not edge_exists:
                random_weight = random.randint(1, 100)
                while random_weight in existing_weights:
                    random_weight = random.randint(1, 100)

                existing_weights.add(random_weight)
                self.add_edge(n1_label, n2_label, random_weight)

# =================================================================================
#  FUNÇÕES AUXILIARES INDEPENDENTES PARA CÁLCULOS COM NETWORKX
# =================================================================================

def build_nx_graph_from_matrix(labels, matrix, is_directed=False):
    G = nx.DiGraph() if is_directed else nx.Graph()
    G.add_nodes_from(labels)
    num_nodes = len(labels)
    for i in range(num_nodes):
        for j in range(num_nodes if is_directed else i, num_nodes):
            if matrix[i][j] > 0:
                G.add_edge(labels[i], labels[j], weight=matrix[i][j])
    return G

def get_all_routes(G, origem, destino, max_nodes=10):
    try:
        return list(nx.all_simple_paths(G, source=origem, target=destino, cutoff=max_nodes))
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []

def get_shortest_path(G, origem, destino):
    try:
        return nx.shortest_path(G, source=origem, target=destino, weight='weight')
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []

def get_longest_safe_path(G, origem, destino, all_routes):
    if not all_routes: return []
    longest_path, max_weight = [], -1.0
    for path in all_routes:
        current_weight = sum(G[u][v]['weight'] for i in range(len(path) - 1) if (u := path[i], v := path[i + 1]))
        if current_weight > max_weight:
            max_weight = current_weight
            longest_path = path
    return longest_path