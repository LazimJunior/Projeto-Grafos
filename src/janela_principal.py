import random
import sys
import math
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QMessageBox, QFrame, QLabel,
    QGraphicsDropShadowEffect, QStatusBar, QFileDialog
)
from PyQt5.QtGui import QIcon, QColor, QFont
from PyQt5.QtCore import Qt
from grafo import GraphView, build_nx_graph_from_matrix, get_all_routes, get_shortest_path, get_longest_safe_path

import resources_rc

# =================================================================================
#  NOVA FOLHA DE ESTILOS (QSS)
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
    transition: background-color 0.2s ease-in-out; 
}
QPushButton:hover {
    background-color: #81A1C1;
}
QPushButton:pressed {
    background-color: #8FBCBB;
}

QStatusBar {
    font-size: 13px;
    color: #D8DEE9;
}
QStatusBar::item {
    border: none;
}
"""


class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Projeto Grafos")
        self.setStyleSheet(POLISHED_STYLESHEET)
        self.setMinimumSize(1200, 800)
        self.setWindowIcon(QIcon(":/icons/random.png"))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        self.graph_view = GraphView()
        main_layout.addWidget(self.graph_view, stretch=3)

        controls_panel = QFrame()
        controls_panel.setObjectName("ControlPanel")
        controls_panel.setFixedWidth(380)
        controls_layout = QVBoxLayout(controls_panel)
        controls_layout.setContentsMargins(15, 15, 15, 15)

        controls_layout.addWidget(self.create_title_label("Matriz de Adjacência"))
        self.adj_matrix_edit = QTextEdit()
        controls_layout.addWidget(self.adj_matrix_edit, stretch=2)

        controls_layout.addWidget(self.create_title_label("Parâmetros do Caminho"))
        path_layout = QHBoxLayout()
        self.origin_edit = QLineEdit();
        self.origin_edit.setPlaceholderText("Origem (ex: A)")
        self.dest_edit = QLineEdit();
        self.dest_edit.setPlaceholderText("Destino (ex: D)")
        path_layout.addWidget(self.origin_edit);
        path_layout.addWidget(self.dest_edit)
        controls_layout.addLayout(path_layout)

        controls_layout.addWidget(self.create_title_label("Ações"))
        self.calc_routes_btn = QPushButton(" Calcular Rotas");
        self.calc_routes_btn.setIcon(QIcon(":/icons/calculate.png"))
        self.generate_matrix_btn = QPushButton(" Gerar Matriz");
        self.generate_matrix_btn.setIcon(QIcon(":/icons/matrix.png"))
        self.random_graph_btn = QPushButton(" Grafo Aleatório");
        self.random_graph_btn.setIcon(QIcon(":/icons/random.png"))
        self.delete_graph_btn = QPushButton(" Limpar");
        self.delete_graph_btn.setIcon(QIcon(":/icons/delete.png"))
        self.save_graph_btn = QPushButton(" Salvar Grafo (TXT)");
        # self.save_graph_btn.setIcon(QIcon(":/icons/save.png"))

        controls_layout.addWidget(self.calc_routes_btn);
        controls_layout.addWidget(self.generate_matrix_btn);
        controls_layout.addWidget(self.random_graph_btn);
        controls_layout.addWidget(self.delete_graph_btn);
        controls_layout.addWidget(self.save_graph_btn)

        controls_layout.addWidget(self.create_separator())

        controls_layout.addWidget(self.create_title_label("Resultados"))
        self.routes_output = QTextEdit();
        self.routes_output.setReadOnly(True)
        controls_layout.addWidget(self.routes_output, stretch=3)

        main_layout.addWidget(controls_panel, stretch=1)

        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Pronto.")

        # Conexões dos botões
        self.calc_routes_btn.clicked.connect(self.calc_routes)
        self.generate_matrix_btn.clicked.connect(self.generate_matrix_from_view)
        self.random_graph_btn.clicked.connect(self.generate_random_graph)
        self.delete_graph_btn.clicked.connect(self.delete_graph)
        self.save_graph_btn.clicked.connect(self.save_graph_data_to_txt)

        self.G = None

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

            if not labels:
                self.adj_matrix_edit.setPlainText("Nenhum nó presente para gerar a matriz de adjacência.")
                self.statusBar().showMessage("Nenhum grafo para gerar matriz.", 4000)
                return

            formatted_matrix_lines = []

            # Cabeçalho das colunas
            # O '    ' inicial é para alinhar com o rótulo da primeira linha
            header_line = "    " + " ".join(f"{label:^3}" for label in labels)
            formatted_matrix_lines.append(header_line)
            formatted_matrix_lines.append("-" * len(header_line))

            # Conteúdo da matriz com rótulos de linha
            for i, row_label in enumerate(labels):
                row_values = " ".join(f"{val:^3}" for val in mat[i])
                formatted_matrix_lines.append(f"{row_label:^3} | {row_values}")

            self.adj_matrix_edit.setPlainText("\n".join(formatted_matrix_lines))
            self.statusBar().showMessage("Matriz gerada a partir da visualização.", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar matriz: {e}")
            self.statusBar().showMessage(f"Erro ao gerar matriz: {e}", 4000)

    def delete_graph(self):
        try:
            self.graph_view.clear()
            self.adj_matrix_edit.clear()
            self.routes_output.clear()
            self.origin_edit.clear()
            self.dest_edit.clear()
            self.G = None
            self.statusBar().showMessage("Grafo e todos os dados apagados.", 4000)
            QMessageBox.information(self, "Grafo Excluído", "O grafo e todos os dados foram removidos com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao excluir o grafo: {e}")

    def save_graph_data_to_txt(self):
        labels, matrix = self.graph_view.generate_adjacency_matrix()
        routes_content = self.routes_output.toPlainText()

        if not labels and not routes_content.strip():
            QMessageBox.warning(self, "Aviso", "Não há dados de grafo ou resultados de rotas para salvar.")
            self.statusBar().showMessage("Nenhum dado para salvar.", 3000)
            return

        file_name, _ = QFileDialog.getSaveFileName(self, "Salvar Dados do Grafo", "dados_grafo.txt",
                                                   "Arquivos de Texto (*.txt);;Todos os Arquivos (*)")

        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write("========== MATRIZ DE ADJACÊNCIA ==========\n")
                    if labels:
                        header_line = "    " + " ".join(f"{label:^3}" for label in labels) + "\n"
                        f.write(header_line)
                        f.write("-" * len(header_line) + "\n")

                        for i, row_label in enumerate(labels):
                            row_values = " ".join(f"{val:^3}" for val in matrix[i])
                            f.write(f"{row_label:^3} | {row_values}\n")
                    else:
                        f.write("Nenhum nó presente para gerar a matriz de adjacência.\n")
                    f.write("\n\n")

                    f.write("========== RESULTADOS DAS ROTAS ==========\n")
                    if routes_content.strip():
                        f.write(routes_content)
                    else:
                        f.write("Nenhum resultado de rota calculado.\n")
                    f.write("\n\n")

                self.statusBar().showMessage(f"Dados do grafo salvos em: {file_name}", 5000)
                QMessageBox.information(self, "Salvar Grafo", f"Dados do grafo salvos com sucesso em:\n{file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar os dados do grafo: {e}")
                self.statusBar().showMessage("Falha ao salvar dados do grafo.", 5000)

    def calc_routes(self):
        text = self.adj_matrix_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Aviso", "A matriz de adjacência está vazia!");
            return
        try:
            lines = text.splitlines()
            matrix = []
            labels_from_input_matrix = []

            is_formatted_matrix = False
            if len(lines) > 2:
                # Verifica se a primeira linha contém caracteres alfabéticos (rótulos dos nós)
                # e se a segunda linha é composta principalmente por hifens (separador)
                has_alpha_in_header = any(c.isalpha() for c in lines[0])
                is_separator_line = all(c == '-' or c.isspace() for c in lines[1].strip())

                if has_alpha_in_header and is_separator_line:
                    is_formatted_matrix = True

            if is_formatted_matrix:
                # Extrai os rótulos da linha do cabeçalho
                header_parts = lines[0].strip().split()
                # Filtra apenas os rótulos (caracteres alfabéticos)
                labels_from_input_matrix = [p for p in header_parts if p.isalpha()]

                # Combina os dados da matriz, ignorando os rótulos de linha e o separador
                for line in lines[2:]: # Começa a partir das linhas de dados reais
                    parts = line.split('|')
                    if len(parts) > 1:
                        # A parte numérica está após o '|'
                        values_str = parts[1].strip().split()
                        matrix.append([int(val) for val in values_str])
                    else:
                        # Se uma linha não tiver um '|' em uma matriz formatada, dará ERRO
                        raise ValueError("Formato de linha da matriz inválido (sem '|' esperado).")
            else:
                # Se não estiver formatado, tentar combinar como uma matriz simples separada por espaços
                for line in lines:
                    values_str = [s for s in line.split() if s] # Filtra strings vazias
                    if values_str:
                        matrix.append([int(s) for s in values_str])

            if not matrix:
                raise ValueError("Matriz de adjacência não pôde ser combinada ou está vazia.")

        except ValueError as e:
            QMessageBox.warning(self, "Erro", f"Matriz inválida! Verifique o formato ou os valores inseridos. Detalhe: {e}");
            return
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro inesperado ao combinar a matriz: {e}")
            return

        n = len(matrix)
        if n == 0:
            QMessageBox.warning(self, "Aviso", "A matriz não contém dados válidos.");
            return

        if any(len(row) != n for row in matrix):
            QMessageBox.warning(self, "Erro", "Matriz de adjacência deve ser quadrada!")
            return

        # Garante que os rótulos sejam consistentes com o tamanho da matriz combinada.
        # Se os rótulos foram extraídos da entrada formatada e correspondem ao tamanho da matriz, use-os.
        # Caso contrário, gere A, B, C... com base no tamanho da matriz.
        if labels_from_input_matrix and len(labels_from_input_matrix) == len(matrix):
            labels = labels_from_input_matrix
        else:
            labels = [chr(ord('A') + i) for i in range(len(matrix))] # Usa o tamanho da matriz combinada

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