import networkx as nx
import random
from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsEllipseItem, QGraphicsLineItem,
    QGraphicsTextItem, QGraphicsScene, QGraphicsDropShadowEffect,
    QMessageBox, QInputDialog
)
from PyQt5.QtGui import (QPen, QColor, QFont, QPainter, QBrush, QPolygonF,
                         QPainterPath, QTransform)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QRectF
from math import cos, sin, atan2, pi, sqrt, radians


# =================================================================================
#  ITENS GRÁFICOS (NÓS E ARESTAS)
# =================================================================================

class NodeItem(QGraphicsEllipseItem):
    """Representa um nó (vértice) que pode ser arrastado na cena."""

    def __init__(self, label, x, y, radius=20):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.edges = []
        self.radius = radius
        # Flags que permitem que o item seja móvel e selecionável
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable)
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges)

        self.normal_brush = QBrush(QColor("#5E81AC"))
        self.selected_brush = QBrush(QColor("#88C0D0"))
        self.setBrush(self.normal_brush)
        self.setPen(QPen(QColor("#88C0D0"), 2))

        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor("#88C0D0"))
        self.shadow.setOffset(QPointF(0, 0))

        self.setGraphicsEffect(self.shadow)
        self.shadow.setEnabled(False)
        self.text_item = QGraphicsTextItem(label, self)
        font = QFont("Segoe UI", 11, QFont.Bold)
        self.text_item.setFont(font)
        self.text_item.setDefaultTextColor(QColor("#ECEFF4"))
        self.setPos(x, y)
        self.label = label
        self.set_label(label)  # Centraliza o texto inicial

    def add_edge(self, edge):
        if edge not in self.edges:
            self.edges.append(edge)

    def set_label(self, new_label):
        """Atualiza o rótulo do nó e centraliza o texto."""
        self.label = new_label
        self.text_item.setPlainText(new_label)
        self.text_item.setPos(-self.text_item.boundingRect().width() / 2, -self.text_item.boundingRect().height() / 2)

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_geometry()
        return super().itemChange(change, value)

    def set_selected(self, is_selected):
        self.shadow.setEnabled(is_selected)
        self.setBrush(self.selected_brush if is_selected else self.normal_brush)


class EdgeItem(QGraphicsLineItem):
    """Representa uma aresta, com lógica para desenhar linhas retas ou curvas."""

    def __init__(self, source_node: NodeItem, dest_node: NodeItem, weight: int = 1, is_directed=False):
        super().__init__()
        self.source_node = source_node
        self.dest_node = dest_node
        self.peso = weight
        self.is_directed = is_directed
        self.arrow_size = 12
        self.is_reciprocal = False

        self._path = QPainterPath()
        self.setZValue(-1)
        self.line_pen = QPen(QColor("#4C566A"), 2.5)
        self.setPen(self.line_pen)

        self.text_item_edge = QGraphicsTextItem(str(self.peso))
        font = QFont("Segoe UI", 10)
        self.text_item_edge.setFont(font)
        self.text_item_edge.setDefaultTextColor(QColor("#D8DEE9"))

        self.source_node.add_edge(self)
        self.dest_node.add_edge(self)
        self.update_geometry()

    def add_text_to_scene(self, scene):
        scene.addItem(self.text_item_edge)

    def set_weight(self, weight):
        self.peso = weight
        self.text_item_edge.setPlainText(str(self.peso))

    def boundingRect(self):
        return self._path.boundingRect().adjusted(-20, -20, 20, 20)

    def shape(self):
        return self._path

    def update_geometry(self):
        self.prepareGeometryChange()
        p1 = self.source_node.pos()
        p2 = self.dest_node.pos()

        line_angle_rad = atan2(p2.y() - p1.y(), p2.x() - p1.x())
        source_dx = cos(line_angle_rad) * self.source_node.radius
        source_dy = sin(line_angle_rad) * self.source_node.radius
        start_point = p1 + QPointF(source_dx, source_dy)

        dest_dx = cos(line_angle_rad) * self.dest_node.radius
        dest_dy = sin(line_angle_rad) * self.dest_node.radius
        end_point = p2 - QPointF(dest_dx, dest_dy)

        self._path = QPainterPath(start_point)

        if self.is_reciprocal:
            dx, dy = p2.x() - p1.x(), p2.y() - p1.y()
            mid_point = (start_point + end_point) / 2
            perp_dx, perp_dy = -dy, dx
            norm = sqrt(perp_dx ** 2 + perp_dy ** 2)
            perp_dx, perp_dy = (perp_dx / norm, perp_dy / norm) if norm > 0 else (0, 0)

            offset_distance = 30
            if self.source_node.label > self.dest_node.label:
                offset_distance *= -1

            control_point = mid_point + QPointF(perp_dx * offset_distance, perp_dy * offset_distance)
            self._path.quadTo(control_point, end_point)
        else:
            self._path.lineTo(end_point)

        text_pos = self._path.pointAtPercent(0.5)
        self.text_item_edge.setPos(text_pos)
        self.update()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.line_pen)
        painter.drawPath(self._path)

        if self.is_directed:
            painter.setBrush(QBrush(QColor("#88C0D0")))
            angle_at_end = self._path.angleAtPercent(1)
            self.draw_arrow(painter, self._path.pointAtPercent(1), angle_at_end)

    def draw_arrow(self, painter, point, angle_deg):
        s = self.arrow_size
        arrow_head = QPolygonF([
            QPointF(0, 0),
            QPointF(-s, -s / 2.5),
            QPointF(-s, s / 2.5)
        ])

        transform = QTransform()
        transform.translate(point.x(), point.y())
        transform.rotate(-angle_deg)
        painter.drawPolygon(transform.map(arrow_head))


class GraphView(QGraphicsView):
    graphChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.nodes, self.edges = {}, []
        self.is_directed = False
        self.setBackgroundBrush(QBrush(QColor("#262b33")))
        self.selected_node = None
        self.add_nodes_mode = False
        self.edit_nodes_mode = False
        self.edit_weights_mode = False
        self.delete_mode = False

    def set_graph_type(self, is_directed: bool):
        self.is_directed = is_directed

    def set_add_nodes_mode(self, enabled: bool):
        self.add_nodes_mode = enabled
        self.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)

    def set_edit_nodes_mode(self, enabled: bool):
        self.edit_nodes_mode = enabled
        self.setCursor(Qt.IBeamCursor if enabled else Qt.ArrowCursor)

    def set_edit_weights_mode(self, enabled: bool):
        self.edit_weights_mode = enabled
        self.setCursor(Qt.IBeamCursor if enabled else Qt.ArrowCursor)

    def set_delete_mode(self, enabled: bool):
        self.delete_mode = enabled
        self.setCursor(Qt.CrossCursor if enabled else Qt.ArrowCursor)

    def add_node(self, label, x, y):
        if label in self.nodes: return
        node = NodeItem(label, x, y)
        self.nodes[label] = node
        self.scene.addItem(node)

    def add_edge(self, label1, label2, weight):
        node1, node2 = self.nodes.get(label1), self.nodes.get(label2)
        if not (node1 and node2) or any(e.source_node == node1 and e.dest_node == node2 for e in self.edges):
            return
        new_edge = EdgeItem(node1, node2, weight, self.is_directed)
        if self.is_directed:
            opposite_edge = next((e for e in self.edges if e.source_node == node2 and e.dest_node == node1), None)
            if opposite_edge:
                new_edge.is_reciprocal = True
        self.edges.append(new_edge)
        self.scene.addItem(new_edge)
        new_edge.add_text_to_scene(self.scene)
        new_edge.update_geometry()
        self.graphChanged.emit()

    def delete_edge(self, edge_to_delete):
        if edge_to_delete not in self.edges: return
        opposite_edge = next((e for e in self.edges if
                              e.source_node == edge_to_delete.dest_node and e.dest_node == edge_to_delete.source_node),
                             None)
        if edge_to_delete.scene():
            self.scene.removeItem(edge_to_delete.text_item_edge)
            self.scene.removeItem(edge_to_delete)
        self.edges.remove(edge_to_delete)
        if edge_to_delete in edge_to_delete.source_node.edges: edge_to_delete.source_node.edges.remove(edge_to_delete)
        if edge_to_delete in edge_to_delete.dest_node.edges: edge_to_delete.dest_node.edges.remove(edge_to_delete)
        if opposite_edge:
            opposite_edge.is_reciprocal = False
            opposite_edge.update_geometry()
        self.graphChanged.emit()

    def clear(self):
        self.scene.clear()
        self.nodes, self.edges, self.selected_node = {}, [], None

    def generate_adjacency_matrix(self):
        labels = sorted(self.nodes.keys())
        size = len(labels)
        index_map = {label: i for i, label in enumerate(labels)}
        mat = [[0] * size for _ in range(size)]
        for edge in self.edges:
            i, j = index_map[edge.source_node.label], index_map[edge.dest_node.label]
            mat[i][j] = edge.peso
            if not self.is_directed:
                mat[j][i] = edge.peso
        return labels, mat

    def update_from_matrix(self, labels, matrix):
        self.clear()
        n = len(labels)
        if n == 0: return
        center_x, center_y, radius = self.width() / 2, self.height() / 2, min(self.width(), self.height()) * 0.35
        for i, label in enumerate(labels):
            angle = 2 * pi * i / n
            self.add_node(label, center_x + radius * cos(angle), center_y + radius * sin(angle))
        for i in range(n):
            for j in range(n):
                if matrix[i][j] > 0:
                    if not self.is_directed and j < i: continue
                    self.add_edge(labels[i], labels[j], int(matrix[i][j]))

    def generate_random_nodes(self, n_nodes):
        self.clear()
        if n_nodes <= 0: return
        labels = [chr(ord('A') + i) for i in range(n_nodes)]
        center_x, center_y = self.width() / 2, self.height() / 2
        radius = min(center_x, center_y) * 0.7
        for i, label in enumerate(labels):
            angle = 2 * pi * i / n_nodes
            self.add_node(label, center_x + radius * cos(angle), center_y + radius * sin(angle))
        if n_nodes <= 1: return
        max_edges = random.randint(n_nodes - 1, n_nodes * 2)
        node_keys = list(self.nodes.keys())
        existing_edges, attempts = set(), 0
        while len(self.edges) < max_edges and attempts < max_edges * 10:
            n1, n2 = random.sample(node_keys, 2)
            edge_to_check = tuple(sorted((n1, n2))) if not self.is_directed else (n1, n2)
            if edge_to_check not in existing_edges:
                self.add_edge(n1, n2, random.randint(1, 100))
                existing_edges.add(edge_to_check)
            attempts += 1

    def mousePressEvent(self, event):
        item_clicked = self.itemAt(event.pos())
        node_item = None
        if isinstance(item_clicked, NodeItem):
            node_item = item_clicked
        elif isinstance(item_clicked, QGraphicsTextItem) and isinstance(item_clicked.parentItem(), NodeItem):
            node_item = item_clicked.parentItem()

        # --- MODO: ADICIONAR NÓS ---
        if self.add_nodes_mode:
            if item_clicked is None:
                label = next((chr(ord('A') + i) for i in range(26) if chr(ord('A') + i) not in self.nodes), None)
                if label:
                    self.add_node(label, self.mapToScene(event.pos()).x(), self.mapToScene(event.pos()).y())
                    self.graphChanged.emit()
            return

        # --- MODO: DELETAR ITENS ---
        if self.delete_mode:
            if isinstance(item_clicked, EdgeItem):
                self.delete_edge(item_clicked)
            elif node_item:
                self.delete_node(node_item)
            elif isinstance(item_clicked, QGraphicsTextItem):
                edge_text = next((e for e in self.edges if e.text_item_edge == item_clicked), None)
                if edge_text: self.delete_edge(edge_text)
            return

        # --- MODO: EDITAR RÓTULO DO NÓ ---
        if self.edit_nodes_mode:
            if node_item:
                self.edit_node_label(node_item)
            return

        # --- MODO: EDITAR PESO DA ARESTA ---
        if self.edit_weights_mode:
            edge_to_edit = None
            if isinstance(item_clicked, EdgeItem):
                edge_to_edit = item_clicked
            elif isinstance(item_clicked, QGraphicsTextItem):
                edge_text = next((e for e in self.edges if e.text_item_edge == item_clicked), None)
                if edge_text: edge_to_edit = edge_text
            if edge_to_edit:
                self.edit_edge_weight(edge_to_edit)
                return

        # --- LÓGICA DE SELEÇÃO E CRIAÇÃO DE ARESTAS (MODO PADRÃO) ---
        if node_item:
            if self.selected_node:
                if self.selected_node != node_item:
                    weight, ok = QInputDialog.getInt(self, "Peso da Aresta", "Digite o peso:", 1, 1, 999)
                    if ok: self.add_edge(self.selected_node.label, node_item.label, weight)
                    self.selected_node.set_selected(False)
                    self.selected_node = None
                else:
                    self.selected_node.set_selected(False)
                    self.selected_node = None
                return
            else:
                self.selected_node = node_item
                self.selected_node.set_selected(True)
        elif self.selected_node:
            self.selected_node.set_selected(False)
            self.selected_node = None
        super().mousePressEvent(event)

    def edit_node_label(self, node_item):
        current_label = node_item.label
        new_label, ok = QInputDialog.getText(self, "Alterar Rótulo do Nó", "Novo rótulo:", text=current_label)
        if ok and new_label and new_label != current_label:
            if new_label in self.nodes:
                QMessageBox.warning(self, "Rótulo Inválido", f"O rótulo '{new_label}' já está em uso.")
                return
            self.nodes[new_label] = self.nodes.pop(current_label)
            node_item.set_label(new_label)
            self.graphChanged.emit()

    def edit_edge_weight(self, edge):
        new_weight, ok = QInputDialog.getInt(self, "Alterar Peso", "Novo peso:", edge.peso, 1, 999)
        if ok and new_weight != edge.peso:
            edge.set_weight(new_weight)
            self.graphChanged.emit()

    def delete_node(self, node_to_delete):
        if node_to_delete.label not in self.nodes: return
        edges_to_remove = list(node_to_delete.edges)
        for edge in edges_to_remove:
            self.delete_edge(edge)
        del self.nodes[node_to_delete.label]
        if node_to_delete.scene():
            self.scene.removeItem(node_to_delete)
        self.graphChanged.emit()


# =================================================================================
#  FUNÇÕES DE MANIPULAÇÃO E CÁLCULO DE GRAFO (NETWORKX)
# =================================================================================

def build_nx_graph_from_matrix(labels, matrix, is_directed=False):
    G = nx.DiGraph() if is_directed else nx.Graph()
    G.add_nodes_from(labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            if matrix[i][j] > 0:
                G.add_edge(labels[i], labels[j], weight=matrix[i][j])
    return G


def get_all_routes(G, source, target, max_nodes=None):
    return list(nx.all_simple_paths(G, source=source, target=target, cutoff=max_nodes))


def get_shortest_path(G, source, target):
    try:
        return nx.dijkstra_path(G, source, target, weight='weight')
    except nx.NetworkXNoPath:
        return None


def get_longest_safe_path(G, source, target, all_routes):
    if not all_routes:
        return None
    return max(all_routes, key=lambda path: nx.path_weight(G, path, weight='weight'))


def calcular_e_formatar_rotas(graph_view: 'GraphView', origem: str, destino: str) -> str:
    if not (origem in graph_view.nodes and destino in graph_view.nodes):
        return "Nó de origem ou destino não encontrado no grafo."
    labels, matrix = graph_view.generate_adjacency_matrix()
    G = build_nx_graph_from_matrix(labels, matrix, graph_view.is_directed)
    try:
        all_paths = get_all_routes(G, origem, destino)
        if not all_paths:
            return f"Nenhuma rota encontrada entre {origem} e {destino}."
        paths_with_costs = [{'path': path, 'cost': nx.path_weight(G, path, weight='weight')} for path in all_paths]
        paths_with_costs.sort(key=lambda x: x['cost'])
        resultado_str = f"Análise de Rota de {origem} para {destino}\n" + "=" * 40 + "\n\n"
        melhor_rota = paths_with_costs[0]
        resultado_str += f"🏆 Melhor Rota (Custo Mínimo):\n   - Caminho: {' → '.join(melhor_rota['path'])}\n   - Custo Total: {melhor_rota['cost']}\n\n"
        if len(paths_with_costs) > 1:
            pior_rota = paths_with_costs[-1]
            resultado_str += f"🚧 Pior Rota (Custo Máximo):\n   - Caminho: {' → '.join(pior_rota['path'])}\n   - Custo Total: {pior_rota['cost']}\n\n"
        if len(paths_with_costs) > 2:
            resultado_str += "🗺️ Outras Rotas Possíveis:\n"
            for i, rota_info in enumerate(paths_with_costs[1:-1]):
                resultado_str += f" {i + 1}. Caminho: {' → '.join(rota_info['path'])}\n     Custo: {rota_info['cost']}\n"
        return resultado_str.strip()
    except nx.NetworkXNoPath:
        return f"Nenhuma rota encontrada entre {origem} e {destino}."
    except nx.NodeNotFound:
        return "Nó de origem ou destino não encontrado no grafo."
    except Exception as e:
        return f"Ocorreu um erro inesperado: {e}"