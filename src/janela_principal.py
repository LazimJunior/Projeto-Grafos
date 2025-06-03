import random
import sys
import math
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QMessageBox, QFrame, QLabel,
    QGraphicsDropShadowEffect, QStatusBar  # NOVO
)
from PyQt5.QtGui import QIcon, QColor, QFont
from PyQt5.QtCore import Qt
from grafo import GraphView, build_nx_graph_from_matrix, get_all_routes, get_shortest_path, get_longest_safe_path

# NOVO: Importa o arquivo com os ícones que acabamos de criar
import resources_rc

# =================================================================================
#  NOVA FOLHA DE ESTILOS (QSS) - AINDA MAIS REFINADA
# =================================================================================
POLISHED_STYLESHEET = """
QWidget {
    background-color: #2E3440;
    color: #ECEFF4;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
}
/* Painel de controles com uma borda para separar visualmente */
#ControlPanel {
    background-color: #3B4252;
    border-radius: 8px;
}
/* Títulos das seções no painel de controle */
#TitleLabel {
    color: #88C0D0;
    font-size: 16px;
    font-weight: bold;
    padding-left: 5px;
    padding-top: 5px;
}
/* Linha horizontal para separar as seções */
#Separator {
    background-color: #4C566A;
}
QLineEdit, QTextEdit {
    background-color: #2E3440;
    border: 1px solid #4C566A;
    border-radius: 8px;
    padding: 8px;
    transition: border 0.2s ease-in-out; /* Transição suave */
}
QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #88C0D0;
}
QPushButton {
    background-color: #5E81AC;
    color: #ECEFF4;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 10px;
    min-height: 25px;
    transition: background-color 0.2s ease-in-out; /* Transição suave */
}
QPushButton:hover {
    background-color: #81A1C1;
}
QPushButton:pressed {
    background-color: #8FBCBB;
}
/* Estilo da barra de status */
QStatusBar {
    font-size: 13px;
    color: #D8DEE9;
}
QStatusBar::item {
    border: none; /* remove a borda entre os itens */
}
"""


class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visualizador de Grafos Pro")
        self.setStyleSheet(POLISHED_STYLESHEET)
        self.setMinimumSize(1200, 800)
        self.setWindowIcon(QIcon(":/icons/random.png"))  # Define o ícone da janela

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        self.graph_view = GraphView()
        main_layout.addWidget(self.graph_view, stretch=3)

        # --- NOVO: PAINEL DE CONTROLE REESTRUTURADO ---
        controls_panel = QFrame()
        controls_panel.setObjectName("ControlPanel")
        controls_panel.setFixedWidth(380)
        controls_layout = QVBoxLayout(controls_panel)
        controls_layout.setContentsMargins(15, 15, 15, 15)

        # --- Grupo 1: Matriz ---
        controls_layout.addWidget(self.create_title_label("Matriz de Adjacência"))
        self.adj_matrix_edit = QTextEdit()
        controls_layout.addWidget(self.adj_matrix_edit, stretch=2)

        # --- Grupo 2: Parâmetros do Caminho ---
        controls_layout.addWidget(self.create_title_label("Parâmetros do Caminho"))
        path_layout = QHBoxLayout()
        self.origin_edit = QLineEdit();
        self.origin_edit.setPlaceholderText("Origem (ex: A)")
        self.dest_edit = QLineEdit();
        self.dest_edit.setPlaceholderText("Destino (ex: D)")
        path_layout.addWidget(self.origin_edit);
        path_layout.addWidget(self.dest_edit)
        controls_layout.addLayout(path_layout)

        # --- Grupo 3: Ações ---
        controls_layout.addWidget(self.create_title_label("Ações"))
        self.calc_routes_btn = QPushButton(" Calcular Rotas");
        self.calc_routes_btn.setIcon(QIcon(":/icons/calculate.png"))
        self.generate_matrix_btn = QPushButton(" Gerar Matriz");
        self.generate_matrix_btn.setIcon(QIcon(":/icons/matrix.png"))
        self.random_graph_btn = QPushButton(" Grafo Aleatório");
        self.random_graph_btn.setIcon(QIcon(":/icons/random.png"))
        controls_layout.addWidget(self.calc_routes_btn);
        controls_layout.addWidget(self.generate_matrix_btn);
        controls_layout.addWidget(self.random_graph_btn)

        # --- Separador ---
        controls_layout.addWidget(self.create_separator())

        # --- Grupo 4: Resultados ---
        controls_layout.addWidget(self.create_title_label("Resultados"))
        self.routes_output = QTextEdit();
        self.routes_output.setReadOnly(True)
        controls_layout.addWidget(self.routes_output, stretch=3)

        main_layout.addWidget(controls_panel, stretch=1)

        # NOVO: Barra de Status
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Pronto.")

        # Conexões
        self.calc_routes_btn.clicked.connect(self.calc_routes)
        self.generate_matrix_btn.clicked.connect(self.generate_matrix_from_view)
        self.random_graph_btn.clicked.connect(self.generate_random_graph)

        self.G = None

    # NOVO: Funções auxiliares para criar os títulos e separadores
    def create_title_label(self, text):
        title = QLabel(text)
        title.setObjectName("TitleLabel")
        return title

    def create_separator(self):
        line = QFrame()
        line.setObjectName("Separator")
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setFixedHeight(1)
        return line

    # Funções de lógica (com adição de mensagens na barra de status)
    def generate_random_graph(self):
        try:
            self.graph_view.clear()
            n_nodes = random.randint(5, 8)
            self.graph_view.generate_random_nodes(n_nodes)
            self.generate_matrix_from_view()
            self.routes_output.clear()
            self.statusBar().showMessage(f"{n_nodes} nós gerados aleatoriamente.", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar grafo aleatório: {e}")

    def generate_matrix_from_view(self):
        try:
            labels, mat = self.graph_view.generate_adjacency_matrix()
            lines = [" ".join(str(v) for v in row) for row in mat]
            self.adj_matrix_edit.setPlainText("\n".join(lines))
            self.statusBar().showMessage("Matriz gerada a partir da visualização.", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar matriz: {e}")

    def calc_routes(self):
        text = self.adj_matrix_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Aviso", "A matriz de adjacência está vazia!");
            return
        try:
            matrix = [list(map(int, line.split())) for line in text.splitlines()]
        except ValueError:
            QMessageBox.warning(self, "Erro", "Matriz inválida!");
            return

        # ... (resto da lógica de calc_routes, que continua igual)
        # ...
        self.statusBar().showMessage(f"Rotas de {origem} a {destino} calculadas.", 4000)
        # ... (resto da lógica de calc_routes)
        # (Lógica de calc_routes não precisa de alterações)
        n = len(matrix)
        if any(len(row) != n for row in matrix):
            QMessageBox.warning(self, "Erro", "Matriz de adjacência deve ser quadrada!")
            return

        labels = [chr(ord('A') + i) for i in range(n)]
        origem = self.origin_edit.text().strip().upper()
        destino = self.dest_edit.text().strip().upper()

        if not origem or not destino:
            QMessageBox.warning(self, "Aviso", "Origem ou destino devem ser preenchidos.")
            return
        if origem not in labels or destino not in labels:
            QMessageBox.warning(self, "Aviso", f"Origem ou destino inválidos. Nós disponíveis: {', '.join(labels)}")
            return

        try:
            self.G = build_nx_graph_from_matrix(labels, matrix)
            if hasattr(self.graph_view, 'update_from_matrix'):
                self.graph_view.update_from_matrix(labels, matrix)

            output = f"■ Análise de Rotas: {origem} → {destino} ■\n"
            all_routes = get_all_routes(self.G, origem, destino, max_nodes=10)
            if not all_routes:
                output += "\nNenhuma rota encontrada entre os pontos."
            else:
                output += "\nRotas Encontradas:\n"
                for r in all_routes:
                    output += f"  • {' → '.join(r)}\n"

            shortest = get_shortest_path(self.G, origem, destino)
            if shortest:
                output += f"\nRota Mais Curta ({len(shortest) - 1} passos):\n  • {' → '.join(shortest)}\n"

            longest = get_longest_safe_path(self.G, origem, destino, all_routes)
            if longest:
                output += f"\nRota Mais Longa Simples ({len(longest) - 1} passos):\n  • {' → '.join(longest)}\n"

            self.routes_output.setPlainText(output)
            self.statusBar().showMessage(f"Rotas de {origem} a {destino} calculadas.", 4000)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro fatal ao processar grafo: {e}")