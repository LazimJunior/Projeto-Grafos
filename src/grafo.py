import networkx as nx
from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsEllipseItem, QGraphicsLineItem,
    QGraphicsTextItem, QGraphicsScene, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QPen, QColor, QFont, QPainter, QBrush
from PyQt5.QtCore import Qt
from math import cos, sin


# =================================================================================
#  ITENS GRÁFICOS CUSTOMIZADOS (NÓS E ARESTAS)
# =================================================================================

class NodeItem(QGraphicsEllipseItem):
    """Representa um nó (vértice) que pode ser arrastado na cena."""

    def __init__(self, label, x, y, radius=20):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable)
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges)

        self.normal_brush = QBrush(QColor("#5E81AC"))  # Cor principal do botão do tema
        self.selected_brush = QBrush(QColor("#88C0D0"))  # Cor de destaque do tema

        self.setBrush(self.normal_brush)
        self.setPen(QPen(QColor("#88C0D0"), 2))  # Borda com cor de destaque

        # Efeito de brilho para seleção
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor("#88C0D0"))
        self.shadow.setOffset(0, 0)
        self.shadow.setEnabled(False)  # Começa desabilitado
        self.setGraphicsEffect(self.shadow)

        self.text_item = QGraphicsTextItem(label, self)  # Renomeado para evitar conflito com self.text de EdgeItem
        font = QFont("Segoe UI", 11, QFont.Bold)
        self.text_item.setFont(font)
        self.text_item.setDefaultTextColor(QColor("#ECEFF4"))  # Cor de texto do tema
        self.text_item.setPos(-self.text_item.boundingRect().width() / 2,
                              -self.text_item.boundingRect().height() / 2)

        self.setPos(x, y)
        self.edges = []
        self.label = label

    def add_edge(self, edge):
        self.edges.append(edge)

    def itemChange(self, change, value):
        # Atualiza a posição das arestas quando o nó é movido
        if change == QGraphicsEllipseItem.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_position()
        return super().itemChange(change, value)

    def set_selected(self, is_selected):
        """Controla o destaque visual do nó."""
        self.shadow.setEnabled(is_selected)
        self.setBrush(self.selected_brush if is_selected else self.normal_brush)


class EdgeItem(QGraphicsLineItem):
    """Representa uma aresta (ligação) entre dois nós."""

    def __init__(self, source_node: NodeItem, dest_node: NodeItem):  # Renomeado os parâmetros
        super().__init__()
        self.source_node = source_node  # Renomeado
        self.dest_node = dest_node  # Renomeado
        self.peso = 1

        self.setPen(QPen(QColor("#4C566A"), 2.5))  # Cor sutil do tema

        # Texto para exibir o peso da aresta
        self.text_item_edge = QGraphicsTextItem(str(self.peso))  # Renomeado
        font = QFont("Segoe UI", 10)
        self.text_item_edge.setFont(font)
        self.text_item_edge.setDefaultTextColor(QColor("#D8DEE9"))
        self.text_item_edge.setZValue(1)  # Para o texto ficar sobre a aresta

        self.source_node.add_edge(self)
        self.dest_node.add_edge(self)
        self.update_position()

    def add_text_to_scene(self, scene):
        scene.addItem(self.text_item_edge)  # Renomeado

    def update_position(self):
        # Atualiza a linha da aresta
        src_pos = self.source_node.pos()  # Renomeado
        dst_pos = self.dest_node.pos()  # Renomeado
        self.setLine(src_pos.x(), src_pos.y(), dst_pos.x(), dst_pos.y())

        # Atualiza o texto do peso para o meio da aresta
        mid_x = (src_pos.x() + dst_pos.x()) / 2
        mid_y = (src_pos.y() + dst_pos.y()) / 2
        self.text_item_edge.setPos(mid_x, mid_y)  # Renomeado

        # Calcula um peso simples baseado na distância
        dist = ((src_pos.x() - dst_pos.x()) ** 2 + (src_pos.y() - dst_pos.y()) ** 2) ** 0.5
        self.peso = max(1, int(dist / 50))
        self.text_item_edge.setPlainText(str(self.peso))  # Renomeado


class GraphView(QGraphicsView):
    """A área de visualização principal que controla a cena gráfica."""

    def __init__(self):
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.nodes = {}  # Dicionário para guardar os nós (label -> NodeItem)
        self.edges = []  # Lista de EdgeItems

        self.setBackgroundBrush(QBrush(QColor("#262b33")))  # Cor de fundo integrada ao tema
        self.selected_node = None

    def add_node(self, label, x, y):
        if label in self.nodes: return
        node = NodeItem(label, x, y)
        self.nodes[label] = node
        self.scene.addItem(node)

    def add_edge(self, label1, label2):
        if label1 not in self.nodes or label2 not in self.nodes: return
        node1 = self.nodes[label1]
        node2 = self.nodes[label2]

        for edge in self.edges:
            if (edge.source_node == node1 and edge.dest_node == node2) or \
                    (edge.source_node == node2 and edge.dest_node == node1):
                return

        edge = EdgeItem(node1, node2)
        self.edges.append(edge)
        self.scene.addItem(edge)
        edge.add_text_to_scene(self.scene)

    def clear(self):
        self.scene.clear()  # Isso remove todos os itens da cena, incluindo QGraphicsTextItems adicionados separadamente.
        self.nodes = {}
        self.edges = []
        self.selected_node = None
        # A barra de status será atualizada pela janela principal se necessário.

    def generate_adjacency_matrix(self):
        labels = sorted(self.nodes.keys())
        size = len(labels)
        index_map = {label: i for i, label in enumerate(labels)}  # Renomeado para evitar conflito com 'index'
        mat = [[0] * size for _ in range(size)]

        for edge in self.edges:
            try:
                i = index_map[edge.source_node.label]  # Renomeado
                j = index_map[edge.dest_node.label]  # Renomeado
                mat[i][j] = edge.peso
                mat[j][i] = edge.peso
            except KeyError:
                # Pode acontecer se um nó foi removido de self.nodes mas a aresta ainda existe
                # Isso não deve acontecer com a lógica atual de clear()
                print(
                    f"Aviso: Chave não encontrada ao gerar matriz para aresta entre {edge.source_node.label} e {edge.dest_node.label}")
                continue
        return labels, mat

    def update_from_matrix(self, labels, matrix):
        """Redesenha o grafo a partir de uma matriz de adjacência."""
        self.clear()
        n = len(labels)
        if n == 0: return

        center_x, center_y = self.width() / 2, self.height() / 2
        radius = min(center_x, center_y) * 0.7 if center_x > 0 else 100

        for i, label in enumerate(labels):
            angle = 2 * 3.1415926535 * i / n  # Usando valor mais preciso de Pi
            x = center_x + cos(angle) * radius
            y = center_y + sin(angle) * radius
            self.add_node(label, x, y)

        for i in range(n):
            for j in range(i, n):  # Evita adicionar arestas duas vezes e auto-loops (j=i) se não desejado
                if matrix[i][j] > 0:
                    self.add_edge(labels[i], labels[j])
                    # Ajusta o peso da aresta se a matriz tiver pesos diferentes do calculado pela distância
                    # Isso requer encontrar a aresta recém-adicionada, o que pode ser um pouco complexo
                    # Por simplicidade, o peso será recalculado pela distância no EdgeItem.

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            item_at = self.itemAt(event.pos())

            current_node_item = None
            if isinstance(item_at, NodeItem):
                current_node_item = item_at
            elif isinstance(item_at, QGraphicsTextItem) and isinstance(item_at.parentItem(), NodeItem):
                current_node_item = item_at.parentItem()

            if current_node_item:  # Clique em um nó existente
                if self.selected_node is None:
                    self.selected_node = current_node_item
                    self.selected_node.set_selected(True)
                    if self.window() and hasattr(self.window(), 'statusBar'):
                        self.window().statusBar().showMessage(f"Nó '{self.selected_node.label}' selecionado.")
                else:
                    if current_node_item != self.selected_node:
                        self.add_edge(self.selected_node.label, current_node_item.label)

                    self.selected_node.set_selected(False)
                    self.selected_node = None
                    if self.window() and hasattr(self.window(), 'statusBar'):
                        self.window().statusBar().showMessage("Pronto.")
            else:  # Clique em área vazia para criar um novo nó
                if self.selected_node:
                    self.selected_node.set_selected(False)
                    self.selected_node = None
                    if self.window() and hasattr(self.window(), 'statusBar'):
                        self.window().statusBar().showMessage("Pronto.")
                else:
                    # Lógica de criação de rótulo A-Z aprimorada
                    if len(self.nodes) >= 26:  # Limite de A a Z
                        QMessageBox.information(self, "Limite Atingido",
                                                "Não é possível adicionar mais nós automaticamente (limite A-Z).")
                        if self.window() and hasattr(self.window(), 'statusBar'):
                            self.window().statusBar().showMessage(
                                "Limite de nós (A-Z) para criação automática atingido.", 4000)
                        super().mousePressEvent(event)  # Chama o método pai para qualquer outro comportamento
                        return

                    # Encontra a primeira letra disponível de A a Z
                    label = None
                    for i in range(26):
                        potential_label = chr(ord('A') + i)
                        if potential_label not in self.nodes:
                            label = potential_label
                            break

                    if label is None:
                        # Isso não deveria acontecer se len(self.nodes) < 26, mas é uma segurança.
                        # Pode indicar que todos os rótulos A-Z já estão em uso por algum motivo.
                        QMessageBox.warning(self, "Erro de Rótulo",
                                            "Não foi possível gerar um rótulo único (A-Z). Todos parecem estar em uso.")
                        super().mousePressEvent(event)
                        return

                    self.add_node(label, scene_pos.x(), scene_pos.y())
                    if self.window() and hasattr(self.window(), 'statusBar'):
                        self.window().statusBar().showMessage(f"Nó '{label}' criado.", 3000)

        super().mousePressEvent(event)

    def generate_random_nodes(self, n_nodes):
        """Gera nós e arestas aleatoriamente."""
        import random  # math.cos e math.sin já estão importados no topo do arquivo
        self.clear()  # Limpa o grafo antes de gerar um novo
        labels = [chr(ord('A') + i) for i in range(n_nodes)]

        center_x, center_y = self.width() / 2, self.height() / 2
        radius = min(center_x, center_y) * 0.7 if center_x > 0 and center_y > 0 else 100

        for i, label in enumerate(labels):
            if n_nodes == 0: break  # Evita divisão por zero se n_nodes for 0
            angle = 2 * 3.1415926535 * i / n_nodes
            x = center_x + radius * cos(angle)
            y = center_y + radius * sin(angle)
            self.add_node(label, x, y)

        edges_added = set()
        # Limita o número máximo de arestas para não sobrecarregar visualmente
        max_edges = min(n_nodes * (n_nodes - 1) // 2, n_nodes + random.randint(0, n_nodes // 2))

        # Garante que temos nós para criar arestas
        node_keys = list(self.nodes.keys())
        if len(node_keys) < 2: return  # Não é possível criar arestas com menos de 2 nós

        while len(self.edges) < max_edges:
            n1_label, n2_label = random.sample(node_keys, 2)

            # Verifica se a aresta já existe (considerando a ordem)
            edge_exists = False
            for edge in self.edges:
                if (edge.source_node.label == n1_label and edge.dest_node.label == n2_label) or \
                        (edge.source_node.label == n2_label and edge.dest_node.label == n1_label):
                    edge_exists = True
                    break
            if not edge_exists:
                self.add_edge(n1_label, n2_label)

            # Para evitar loop infinito se todos os pares possíveis já foram adicionados
            if len(self.edges) >= n_nodes * (n_nodes - 1) // 2:
                break


# =================================================================================
#  FUNÇÕES AUXILIARES INDEPENDENTES PARA CÁLCULOS COM NETWORKX
# =================================================================================

def build_nx_graph_from_matrix(labels, matrix):
    """Cria um objeto de grafo do NetworkX a partir de uma matriz de adjacência."""
    G = nx.Graph()
    G.add_nodes_from(labels)
    num_nodes = len(labels)
    if num_nodes != len(matrix):  # Verificação básica de consistência
        print("Aviso: Número de rótulos não corresponde à dimensão da matriz.")
        return G  # Retorna grafo vazio ou parcialmente construído

    for i in range(num_nodes):
        if len(matrix[i]) != num_nodes:  # Verifica se cada linha tem o tamanho correto
            print(f"Aviso: Linha {i} da matriz tem tamanho incorreto.")
            continue
        for j in range(i, num_nodes):
            if matrix[i][j] > 0:
                G.add_edge(labels[i], labels[j], weight=matrix[i][j])
    return G


def get_all_routes(G, origem, destino, max_nodes=10):
    """Encontra todos os caminhos simples entre dois nós."""
    if not G.has_node(origem) or not G.has_node(destino):
        return []
    try:
        return list(nx.all_simple_paths(G, source=origem, target=destino, cutoff=max_nodes))
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []


def get_shortest_path(G, origem, destino):
    """Encontra o caminho mais curto (considerando o peso) entre dois nós."""
    if not G.has_node(origem) or not G.has_node(destino):
        return []
    try:
        return nx.shortest_path(G, source=origem, target=destino, weight='weight')
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []  # Retorna lista vazia para consistência


def get_longest_safe_path(G, origem, destino, all_routes):
    """Encontra o caminho 'mais longo' (maior soma de pesos) a partir de uma lista de rotas."""
    if not all_routes: return []
    if not G.has_node(origem) or not G.has_node(destino):
        return []

    longest_path = []
    max_weight = -1.0  # Usar float para pesos

    for path in all_routes:
        current_weight = 0.0
        valid_path = True
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            if G.has_edge(u, v) and 'weight' in G[u][v]:
                current_weight += G[u][v]['weight']
            else:
                # print(f"Aviso: Aresta ({u}-{v}) ou peso não encontrado no grafo para o caminho {path}")
                valid_path = False
                break

        if valid_path and current_weight > max_weight:
            max_weight = current_weight
            longest_path = path

    return longest_path