import random
import sys
import math
import networkx as nx
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QMessageBox, QFrame, QLabel,
    QGraphicsDropShadowEffect, QStatusBar, QFileDialog, QDialog,
    QDialogButtonBox, QSpinBox, QGridLayout, QFormLayout, QComboBox
)
from PyQt5.QtGui import QIcon, QColor, QFont
from PyQt5.QtCore import Qt, QPointF
from grafo import GraphView, build_nx_graph_from_matrix, get_all_routes, get_shortest_path, get_longest_safe_path

# =================================================================================
#  FOLHA DE ESTILOS (QSS)
# =================================================================================
POLISHED_STYLESHEET = """
QWidget {
    background-color: #2E3440;
    color: #ECEFF4;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
}
#ControlPanel {
    background-color: #3B4252;
    border-radius: 8px;
}
#TitleLabel {
    color: #88C0D0;
    font-size: 16px;
    font-weight: bold;
    padding-left: 5px;
    padding-top: 5px;
}
#Separator {
    background-color: #4C566A;
}
QLineEdit, QTextEdit, QComboBox {
    background-color: #2E3440;
    border: 1px solid #4C566A;
    border-radius: 8px;
    padding: 8px;
    transition: border 0.2s ease-in-out;
}
QComboBox::drop-down {
    border: none;
}
QComboBox::down-arrow {
    image: url(:/icons/down-arrow.png);
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #88C0D0;
}
QPushButton {
    background-color: #5E81AC;
    color: #ECEFF4;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 8px;
    min-height: 20px;
    transition: background-color 0.2s ease-in-out;
}
QPushButton:hover {
    background-color: #81A1C1;
}
QPushButton:pressed {
    background-color: #8FBCBB;
}
QPushButton:checked {
    background-color: #88C0D0;
    color: #2E3440;
    border: 1px solid #ECEFF4;
}
QStatusBar {
    font-size: 13px;
    color: #D8DEE9;
}
QStatusBar::item {
    border: none;
}
"""


# =================================================================================
#  JANELA DE DIÁLOGO PARA CRIAÇÃO DA MATRIZ
# =================================================================================
class MatrixInputDialog(QDialog):
    def __init__(self, is_directed=False, parent=None):
        super().__init__(parent)
        self.is_directed = is_directed
        title = "Criar Matriz (Orientado)" if is_directed else "Criar Matriz (Não-Orientado)"
        self.setWindowTitle(title)
        self.setMinimumWidth(350)

        self.layout = QVBoxLayout(self)
        self.step1_widget = QWidget()
        step1_layout = QFormLayout(self.step1_widget)
        self.nodes_spinbox = QSpinBox()
        self.nodes_spinbox.setRange(2, 26)
        self.nodes_spinbox.setValue(4)
        step1_layout.addRow("Número de Nós:", self.nodes_spinbox)
        self.layout.addWidget(self.step1_widget)

        self.step2_widget = QWidget()
        self.grid_layout = QGridLayout(self.step2_widget)
        self.layout.addWidget(self.step2_widget)
        self.step2_widget.hide()

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.next_button = QPushButton("Gerar Tabela")
        self.button_box.addButton(self.next_button, QDialogButtonBox.ActionRole)
        self.layout.addWidget(self.button_box)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

        self.next_button.clicked.connect(self.create_matrix_grid)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.matrix_inputs = []
        self.labels = []

    def create_matrix_grid(self):
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        num_nodes = self.nodes_spinbox.value()
        self.labels = [chr(ord('A') + i) for i in range(num_nodes)]
        self.matrix_inputs = [[None] * num_nodes for _ in range(num_nodes)]

        for j, label in enumerate(self.labels):
            self.grid_layout.addWidget(QLabel(f"<b>{label}</b>"), 0, j + 1, Qt.AlignCenter)

        for i, label in enumerate(self.labels):
            self.grid_layout.addWidget(QLabel(f"<b>{label}</b>"), i + 1, 0)
            for j in range(num_nodes):
                line_edit = QLineEdit("0")
                line_edit.setFixedWidth(40)
                line_edit.setAlignment(Qt.AlignCenter)

                if i == j:
                    line_edit.setDisabled(True)
                elif not self.is_directed:
                    if j < i:
                        line_edit.setDisabled(True)
                    else:
                        line_edit.textChanged.connect(
                            lambda text, r=i, c=j: self.update_symmetric_value(text, r, c)
                        )
                self.grid_layout.addWidget(line_edit, i + 1, j + 1)
                self.matrix_inputs[i][j] = line_edit

        self.step1_widget.hide()
        self.next_button.hide()
        self.step2_widget.show()
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
        self.adjustSize()

    def update_symmetric_value(self, text, row, col):
        if self.matrix_inputs[col][row]:
            self.matrix_inputs[col][row].setText(text)

    def get_matrix_data(self):
        num_nodes = len(self.labels)
        matrix = [[0] * num_nodes for _ in range(num_nodes)]
        for i in range(num_nodes):
            for j in range(num_nodes):
                try:
                    matrix[i][j] = int(self.matrix_inputs[i][j].text())
                except (ValueError, TypeError):
                    matrix[i][j] = 0
        return self.labels, matrix


class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Projeto Grafos")
        self.setStyleSheet(POLISHED_STYLESHEET)
        self.setMinimumSize(1200, 800)

        self.is_directed = False

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        self.graph_view = GraphView()
        self.graph_view.graphChanged.connect(self.generate_matrix_from_view)
        main_layout.addWidget(self.graph_view, stretch=3)

        controls_panel = QFrame()
        controls_panel.setObjectName("ControlPanel")
        controls_panel.setFixedWidth(380)
        controls_layout = QVBoxLayout(controls_panel)
        controls_layout.setContentsMargins(15, 15, 15, 15)

        controls_layout.addWidget(self.create_title_label("Matriz de Adjacência"))
        self.adj_matrix_edit = QTextEdit()
        controls_layout.addWidget(self.adj_matrix_edit, stretch=2)

        controls_layout.addWidget(self.create_title_label("Tipo de Grafo"))
        self.graph_type_combo = QComboBox()
        self.graph_type_combo.addItems(["Não-Orientado", "Orientado"])
        controls_layout.addWidget(self.graph_type_combo)

        controls_layout.addWidget(self.create_title_label("Parâmetros do Caminho"))
        path_layout = QHBoxLayout()
        self.origin_edit = QLineEdit()
        self.origin_edit.setPlaceholderText("Origem (ex: A)")
        self.dest_edit = QLineEdit()
        self.dest_edit.setPlaceholderText("Destino (ex: D)")
        path_layout.addWidget(self.origin_edit)
        path_layout.addWidget(self.dest_edit)
        controls_layout.addLayout(path_layout)

        controls_layout.addWidget(self.create_title_label("Modos de Edição"))

        modes_layout = QGridLayout()
        modes_layout.setSpacing(10)
        self.add_nodes_btn = QPushButton("Adicionar Nó")
        self.add_nodes_btn.setCheckable(True)
        self.edit_node_btn = QPushButton("Editar Rótulo")
        self.edit_node_btn.setCheckable(True)
        self.edit_weights_btn = QPushButton("Editar Peso")
        self.edit_weights_btn.setCheckable(True)
        self.delete_mode_btn = QPushButton("Excluir Item")
        self.delete_mode_btn.setCheckable(True)

        self.mode_buttons = [self.add_nodes_btn, self.edit_node_btn, self.edit_weights_btn, self.delete_mode_btn]

        modes_layout.addWidget(self.add_nodes_btn, 0, 0)
        modes_layout.addWidget(self.edit_node_btn, 0, 1)
        modes_layout.addWidget(self.edit_weights_btn, 1, 0)
        modes_layout.addWidget(self.delete_mode_btn, 1, 1)
        controls_layout.addLayout(modes_layout)

        controls_layout.addWidget(self.create_title_label("Ações"))
        actions_grid = QGridLayout()
        actions_grid.setSpacing(10)
        self.calc_routes_btn = QPushButton("Calcular Rotas")
        self.generate_matrix_btn = QPushButton("Gerar Matriz do Grafo")
        self.create_matrix_btn = QPushButton("Criar Matriz por Tabela")
        self.random_graph_btn = QPushButton("Grafo Aleatório")
        self.delete_graph_btn = QPushButton("Limpar Tudo")
        self.save_graph_btn = QPushButton("Salvar Grafo (TXT)")
        actions_grid.addWidget(self.calc_routes_btn, 0, 0)
        actions_grid.addWidget(self.generate_matrix_btn, 0, 1)
        actions_grid.addWidget(self.create_matrix_btn, 1, 0)
        actions_grid.addWidget(self.random_graph_btn, 1, 1)
        actions_grid.addWidget(self.delete_graph_btn, 2, 0)
        actions_grid.addWidget(self.save_graph_btn, 2, 1)
        controls_layout.addLayout(actions_grid)

        controls_layout.addWidget(self.create_separator())
        controls_layout.addWidget(self.create_title_label("Resultados"))
        self.routes_output = QTextEdit()
        self.routes_output.setReadOnly(True)
        controls_layout.addWidget(self.routes_output, stretch=3)

        main_layout.addWidget(controls_panel, stretch=1)

        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Pronto.")

        self.graph_type_combo.currentIndexChanged.connect(self.on_graph_type_changed)
        for button in self.mode_buttons:
            button.clicked.connect(self.on_mode_button_toggled)

        self.calc_routes_btn.clicked.connect(self.calc_routes)
        self.generate_matrix_btn.clicked.connect(self.generate_matrix_from_view)
        self.create_matrix_btn.clicked.connect(self.create_matrix_from_input)
        self.random_graph_btn.clicked.connect(self.generate_random_graph)
        self.delete_graph_btn.clicked.connect(self.delete_graph)
        self.save_graph_btn.clicked.connect(self.save_graph_data_to_txt)

    def on_mode_button_toggled(self):
        sender = self.sender()
        is_active = sender.isChecked()

        # Desativa todos os modos no backend
        self.graph_view.set_add_nodes_mode(False)
        self.graph_view.set_edit_nodes_mode(False)
        self.graph_view.set_edit_weights_mode(False)
        self.graph_view.set_delete_mode(False)

        # Desmarca todos os outros botões
        for button in self.mode_buttons:
            if button is not sender:
                button.setChecked(False)

        # Ativa o modo correto se o botão foi ativado
        if is_active:
            if sender == self.add_nodes_btn:
                self.graph_view.set_add_nodes_mode(True)
            elif sender == self.edit_node_btn:
                self.graph_view.set_edit_nodes_mode(True)
            elif sender == self.edit_weights_btn:
                self.graph_view.set_edit_weights_mode(True)
            elif sender == self.delete_mode_btn:
                self.graph_view.set_delete_mode(True)

    def on_graph_type_changed(self, index):
        is_new_mode_directed = (index == 1)
        if is_new_mode_directed == self.is_directed:
            return

        reply = QMessageBox.question(self, 'Mudar Tipo de Grafo',
                                     "Mudar o tipo de grafo irá limpar o cenário atual. Deseja continuar?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.is_directed = is_new_mode_directed
            self.graph_view.set_graph_type(self.is_directed)
            self.delete_graph()
            self.statusBar().showMessage(
                f"Modo alterado para Grafo {'Orientado' if self.is_directed else 'Não-Orientado'}.", 5000)
        else:
            self.graph_type_combo.blockSignals(True)
            self.graph_type_combo.setCurrentIndex(0 if not self.is_directed else 1)
            self.graph_type_combo.blockSignals(False)

    def create_title_label(self, text):
        label = QLabel(text)
        label.setObjectName("TitleLabel")
        return label

    def create_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setFixedHeight(1)
        line.setObjectName("Separator")
        return line

    def create_matrix_from_input(self):
        dialog = MatrixInputDialog(self.is_directed, self)
        if dialog.exec_() == QDialog.Accepted:
            labels, matrix = dialog.get_matrix_data()
            self.graph_view.clear()
            self.routes_output.clear()
            self.graph_view.update_from_matrix(labels, matrix)
            self.update_adj_matrix_text(labels, matrix)
            self.statusBar().showMessage("Matriz criada e grafo atualizado.", 4000)

    def update_adj_matrix_text(self, labels, mat):
        if not labels:
            self.adj_matrix_edit.setPlainText("Nenhum nó presente para gerar a matriz.")
            return
        header = f"    {' '.join(f'{label:^3}' for label in labels)}"
        separator = f"  {'-' * (len(header) - 2)}"
        matrix_str = [header, separator]
        for i, row_label in enumerate(labels):
            row_str = " ".join(f"{val:^3}" for val in mat[i])
            matrix_str.append(f"{row_label:^3}| {row_str}")
        self.adj_matrix_edit.setPlainText("\n".join(matrix_str))

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
            self.update_adj_matrix_text(labels, mat)
            if labels:
                self.statusBar().showMessage("Matriz gerada a partir da visualização.", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar matriz: {e}")

    def delete_graph(self):
        self.graph_view.clear()
        self.adj_matrix_edit.clear()
        self.routes_output.clear()
        self.origin_edit.clear()
        self.dest_edit.clear()
        self.statusBar().showMessage("Cenário limpo.", 4000)

    def save_graph_data_to_txt(self):
        labels, matrix = self.graph_view.generate_adjacency_matrix()
        routes_content = self.routes_output.toPlainText()
        if not labels and not routes_content.strip():
            QMessageBox.warning(self, "Aviso", "Não há dados de grafo ou resultados para salvar.")
            return
        file_name, _ = QFileDialog.getSaveFileName(self, "Salvar Dados do Grafo", "dados_grafo.txt",
                                                   "Arquivos de Texto (*.txt);;Todos os Arquivos (*)")
        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(
                        f"========== MATRIZ DE ADJACÊNCIA (Grafo {'Orientado' if self.is_directed else 'Não-Orientado'}) ==========\n")
                    if labels:
                        header_line = "    " + "  ".join(f"{label:^3}" for label in labels) + "\n"
                        f.write(header_line)
                        f.write("-" * (len(header_line) + 1) + "\n")
                        for i, row_label in enumerate(labels):
                            row_values = " ".join(f"{val:^3}" for val in matrix[i])
                            f.write(f"{row_label:^3} | {row_values}\n")
                    else:
                        f.write("Nenhum nó para gerar a matriz.\n")
                    f.write("\n\n========== RESULTADOS DAS ROTAS ==========\n")
                    f.write(routes_content if routes_content.strip() else "Nenhum resultado de rota calculado.\n")
                self.statusBar().showMessage(f"Dados salvos em: {file_name}", 5000)
                QMessageBox.information(self, "Salvar Grafo", f"Dados salvos com sucesso em:\n{file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar os dados: {e}")

    def get_path_steps_str(self, G, path):
        """Helper para gerar a string de passos detalhados para um caminho."""
        if len(path) < 2:
            return ""
        steps = []
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge_cost = G[u][v]['weight']
            steps.append(f"{u}→{v}: {edge_cost}")
        return f" <span style='color: #A3BE8C; font-size: 13px;'>({', '.join(steps)})</span>"

    def calc_routes(self):
        labels, matrix = self.graph_view.generate_adjacency_matrix()
        if not labels:
            QMessageBox.warning(self, "Aviso", "O grafo está vazio. Adicione nós e arestas primeiro.")
            return
        origem = self.origin_edit.text().strip().upper()
        destino = self.dest_edit.text().strip().upper()
        if not origem or not destino:
            QMessageBox.warning(self, "Aviso", "Origem e destino devem ser preenchidos.")
            return
        if origem not in labels or destino not in labels:
            QMessageBox.warning(self, "Aviso", f"Nós inválidos. Disponíveis: {', '.join(labels)}")
            return
        try:
            G = build_nx_graph_from_matrix(labels, matrix, self.is_directed)
            style = "color: #ECEFF4; font-family: 'Segoe UI', sans-serif; font-size: 14px; line-height: 1.6;"
            html = f"<div style='{style}'>"
            html += f"<h4>■ Análise de Rotas: {origem} → {destino} ■</h4>"
            all_routes = get_all_routes(G, origem, destino, max_nodes=10)

            if not all_routes:
                html += "<p>Nenhuma rota encontrada.</p>"
            else:
                html += "<p><b>Todas as Rotas Simples:</b></p><ul>"
                routes_with_cost = []
                for r in all_routes:
                    cost = nx.path_weight(G, r, 'weight')
                    routes_with_cost.append((r, cost))

                routes_with_cost.sort(key=lambda x: (x[1], len(x[0])))  # Ordena por custo, depois por tamanho

                for r, cost in routes_with_cost:
                    path_str = ' → '.join(r)
                    steps_str = self.get_path_steps_str(G, r)
                    html += f"<li>{path_str} &nbsp; (Custo Total: <b>{cost}</b>){steps_str}</li>"
                html += "</ul><br>"

            if shortest_path := get_shortest_path(G, origem, destino):
                cost = nx.path_weight(G, shortest_path, 'weight')
                path_str = ' → '.join(shortest_path)
                steps_str = self.get_path_steps_str(G, shortest_path)
                html += f"<p><b>🏆 Rota Mais Curta (menor custo):</b><br> &nbsp; &nbsp; {path_str} &nbsp; (Custo: <b>{cost}</b>){steps_str}</p>"

            if longest_path := get_longest_safe_path(G, origem, destino, all_routes):
                cost = nx.path_weight(G, longest_path, 'weight')
                path_str = ' → '.join(longest_path)
                steps_str = self.get_path_steps_str(G, longest_path)
                html += f"<p><b>🧗 Rota Mais Longa Simples:</b><br> &nbsp; &nbsp; {path_str} &nbsp; (Custo: <b>{cost}</b>){steps_str}</p>"

            html += "</div>"
            self.routes_output.setHtml(html)
            self.statusBar().showMessage(f"Rotas de {origem} a {destino} calculadas.", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro fatal ao processar grafo: {e}")