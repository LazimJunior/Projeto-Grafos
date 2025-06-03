import sys
import math
import random
import importlib
import networkx as nx
import gc
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QCheckBox, QTextEdit, QLabel, QGraphicsView,
    QGraphicsScene, QGraphicsEllipseItem, QGraphicsItem, QGraphicsTextItem
)
from PyQt5.QtGui import (
    QBrush, QColor, QPen, QPolygonF, QPainter, QLinearGradient, QFont, QIcon
)
from PyQt5.QtCore import Qt, QPointF, QRectF, QLineF

# ---------------------------
# Classes para exibição interativa do grafo
# ---------------------------

class Node(QGraphicsEllipseItem):
    def __init__(self, x, y, label, radius=20):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.setPos(x, y)
        self.setBrush(QBrush(QColor("#7FB3D5")))
        # noinspection PyTypeChecker
        self.setFlags(
            QGraphicsEllipseItem.ItemIsMovable |
            QGraphicsEllipseItem.ItemIsSelectable |
            QGraphicsEllipseItem.ItemSendsGeometryChanges
        )
        self.edges = []  # Lista de arestas conectadas
        self.label = label

        # Criação e centralização do rótulo
        self.text_item = QGraphicsTextItem(label, self)
        self.text_item.setDefaultTextColor(Qt.white)
        font = QFont("Segoe UI", 10, QFont.Bold)
        self.text_item.setFont(font)
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(-text_rect.width() / 2, -text_rect.height() / 2)

    def add_edge(self, edge):
        self.edges.append(edge)

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update()
        return super().itemChange(change, value)


class Edge(QGraphicsItem):
    def __init__(self, source, dest, oriented=False, weight=None):
        super().__init__()
        self.source = source
        self.dest = dest
        self.oriented = oriented
        self.weight = weight  # Pode ser um número ou None
        self.show_weight = False  # Se True, o peso será desenhado
        self.source.add_edge(self)
        self.dest.add_edge(self)
        # noinspection PyTypeChecker
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setZValue(-1)  # Desenha as arestas atrás dos nós

    def boundingRect(self):
        extra = 5
        p1 = self.source.scenePos()
        p2 = self.dest.scenePos()
        rect = QRectF(p1, p2).normalized()
        return rect.adjusted(-extra, -extra, extra, extra)

    def paint(self, painter, option, widget=None):
        p1 = self.source.scenePos()
        p2 = self.dest.scenePos()
        line = QLineF(p1, p2)
        if line.length() == 0:
            return
        pen = QPen(QColor("#4A4A4A"), 3)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(line)
        if self.oriented:
            self.drawArrow(painter, line)
        if self.show_weight and self.weight is not None:
            midpoint = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            length = math.hypot(dx, dy)
            offset = 12
            perp = QPointF(-dy / length * offset, dx / length * offset) if length != 0 else QPointF(0, 0)
            weight_point = midpoint + perp
            font = QFont("Segoe UI", 8)
            painter.setFont(font)
            text = str(self.weight)
            text_rect = painter.fontMetrics().boundingRect(text)
            text_rect.moveCenter(weight_point.toPoint())
            painter.setPen(QPen(QColor("#4A4A4A")))
            painter.drawText(text_rect, Qt.AlignCenter, text)

    @staticmethod
    def drawArrow(painter, line):
        arrow_size = 10
        angle = math.atan2(line.dy(), line.dx())
        p2 = line.p2()
        dest_arrow_p1 = p2 + QPointF(
            math.sin(angle - math.pi / 3) * arrow_size,
            math.cos(angle - math.pi / 3) * arrow_size
        )
        dest_arrow_p2 = p2 + QPointF(
            math.sin(angle - math.pi + math.pi / 3) * arrow_size,
            math.cos(angle - math.pi + math.pi / 3) * arrow_size
        )
        arrow_head = QPolygonF([p2, dest_arrow_p1, dest_arrow_p2])
        painter.setBrush(QColor("#4A4A4A"))
        painter.drawPolygon(arrow_head)


# ---------------------------
# Interface Integrada
# ---------------------------

class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grafo")
        self.resize(1200, 750)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FBF7F0, stop:1 #F8F2E9);
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #C4AA95;
                border-radius: 8px;
                background-color: #FFFFFF;
                color: #5A4B3C;
            }
            QPushButton {
                background-color: #C4AA95;
                color: #5A4B3C;
                padding: 8px 12px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #B39F89;
            }
            QCheckBox {
                padding: 8px;
                color: #5A4B3C;
            }
            QTextEdit {
                background-color: #FFFFFF;
                padding: 8px;
                border: 1px solid #C4AA95;
                border-radius: 8px;
                color: #5A4B3C;
            }
            QLabel {
                color: #5A4B3C;
                font-size: 16px;
                font-weight: bold;
            }
        """)

        # ESTAS LINHAS FORAM MOVIDAS PARA DENTRO DO __init__
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Área esquerda: controles e área para exibição do grafo interativo
        left_layout = QVBoxLayout()
        main_layout.addLayout(left_layout, stretch=3)

        controls_layout = QHBoxLayout()
        left_layout.addLayout(controls_layout)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Digite conexões:")
        controls_layout.addWidget(self.input_line)
        self.input_line.textChanged.connect(self.on_input_changed)

        self.oriented_checkbox = QCheckBox("Grafo Orientado")
        controls_layout.addWidget(self.oriented_checkbox)

        self.show_weight_checkbox = QCheckBox("Exibir Pesos")
        self.show_weight_checkbox.setChecked(True)
        controls_layout.addWidget(self.show_weight_checkbox)

        self.gen_button = QPushButton("Gerar Grafo")
        self.gen_button.clicked.connect(self.load_grafo_py)  # Grafo com imput
        controls_layout.addWidget(self.gen_button)

        self.rand_button = QPushButton("Gerar Grafo Aleatório")
        self.rand_button.clicked.connect(self.load_random_grafo)  # Grafo Aleatorio
        controls_layout.addWidget(self.rand_button)

        self.clear_button = QPushButton("Limpar")
        self.clear_button.clicked.connect(self.clear_all)
        controls_layout.addWidget(self.clear_button)

        if self.input_line.text().strip() == "":
            self.gen_button.setEnabled(False)

        self.scene = QGraphicsScene()
        grad = QLinearGradient(0, 0, 0, 600)
        grad.setColorAt(0, QColor("#FBF7F0"))
        grad.setColorAt(1, QColor("#F8F2E9"))
        self.scene.setBackgroundBrush(QBrush(grad))
        self.view = QGraphicsView(self.scene)
        self.view.setStyleSheet("border: 2px solid #C4AA95; border-radius: 15px;")
        self.view.setInteractive(True)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        left_layout.addWidget(self.view)

        # Área direita: painel de histórico e painel para a matriz de adjacência
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, stretch=1)

        self.history_label = QLabel("Histórico de Grafos:")
        right_layout.addWidget(self.history_label)
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        right_layout.addWidget(self.history_text)

        self.matrix_label = QLabel("Matriz de Adjacência:")
        right_layout.addWidget(self.matrix_label)
        self.matrix_text = QTextEdit()
        self.matrix_text.setReadOnly(True)
        right_layout.addWidget(self.matrix_text)

        self.history = []


    def load_random_grafo(self):
        """Carrega um grafo aleatório do módulo grafo.py"""
        try:
            import grafo #
            nx_grafo = grafo.get_grafo(None) #
            num_nodes = len(nx_grafo.nodes())
            num_edges = len(nx_grafo.edges())
            self.visualize_graph(nx_grafo)

            # Histórico
            history_entry = f"Grafo aleatório gerado ({num_nodes} nós, {num_edges} arestas)"
            self.history.append(history_entry)
            self.history_text.setPlainText("\n".join(self.history))
        except Exception as e:
            print("Erro ao carregar grafo aleatório:", e)
            self.history_text.append(f"Erro: {str(e)}")


    def load_grafo_py(self):
        """Carrega grafo do input usando grafo.py"""
        try:
            import grafo #
            input_text = self.input_line.text().strip()
            nx_grafo = grafo.get_grafo(input_text if input_text else None) #
            num_nodes = len(nx_grafo.nodes())
            num_edges = len(nx_grafo.edges())
            self.visualize_graph(nx_grafo)

            # Histórico
            history_entry = f"Grafo carregado do input ({num_nodes} nós, {num_edges} arestas)"
            self.history.append(history_entry)
            self.history_text.setPlainText("\n".join(self.history))
        except Exception as e:
            print("Erro ao carregar grafo.py:", e)
            self.history_text.append(f"Erro: {str(e)}")


    def on_input_changed(self, text):
        if text.strip():
            self.gen_button.setEnabled(True)
        else:
            self.gen_button.setEnabled(False)


    def clear_all(self):
        # Limpeza adequada da cena
        for item in self.scene.items():
            self.scene.removeItem(item)
        self.scene.clear()
        self.history.clear()
        self.history_text.clear()
        self.matrix_text.clear()
        gc.collect()  # Adicione import gc no topo


    def visualize_graph(self, nx_grafo):
        """Visualização segura do grafo com verificações de memória"""
        try:
            # Limpa itens anteriores corretamente
            for item in self.scene.items():
                if isinstance(item, (Node, Edge)):
                    self.scene.removeItem(item)

            # Limita tamanho do grafo para estabilidade
            if len(nx_grafo.nodes()) > 50:
                raise ValueError("Grafo muito grande para visualização (máx. 50 nós)")

            pos = nx.spring_layout(nx_grafo, scale=1.0)
            nodes_dict = {}

            # Cria nós
            for node in nx_grafo.nodes():
                x, y = pos[node]
                node_item = Node(x * 300 + 150, y * 300 + 150, str(node))
                self.scene.addItem(node_item)
                nodes_dict[node] = node_item

            # Cria arestas com feedback de progresso
            oriented = self.oriented_checkbox.isChecked()
            edge_count = 0
            for u, v, data in nx_grafo.edges(data=True):
                if edge_count > 200:  # Limite de arestas
                    break
                weight = data.get("peso", None)
                edge_item = Edge(nodes_dict[u], nodes_dict[v], oriented, weight)
                edge_item.show_weight = self.show_weight_checkbox.isChecked()
                self.scene.addItem(edge_item)
                edge_count += 1
                QApplication.processEvents()  # Previne congelamento da UI

            # Atualiza exibição da matriz
            try:
                import grafo #
                A = grafo.get_adjacency_matrix(nx_grafo) #
                import numpy as np
                np.set_printoptions(threshold=10, linewidth=100)
                matrix_str = np.array2string(A.astype(int), separator='\t')
                self.matrix_text.setPlainText(matrix_str)
            except Exception as e:
                print("Erro na matriz:", str(e))

        except Exception as e:
            print("Erro de visualização:", str(e))
            self.history_text.append(f"Erro: {str(e)}")