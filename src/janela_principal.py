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
from grafo import VisualizadorGrafo, construir_grafo_nx_da_matriz, obter_todas_rotas, obter_caminho_mais_curto, \
    obter_caminho_mais_longo_seguro

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

class DialogoEntradaMatriz(QDialog):
    def __init__(self, e_direcionada=False, parent=None):
        super().__init__(parent)
        self.e_direcionada = e_direcionada
        titulo = "Criar Matriz (Orientado)" if e_direcionada else "Criar Matriz (Não-Orientado)"
        self.setWindowTitle(titulo)
        self.setMinimumWidth(350)

        self.layout = QVBoxLayout(self)
        self.widget_passo1 = QWidget()
        layout_passo1 = QFormLayout(self.widget_passo1)
        self.spinbox_nos = QSpinBox()
        self.spinbox_nos.setRange(2, 26)
        self.spinbox_nos.setValue(4)
        layout_passo1.addRow("Número de Nós:", self.spinbox_nos)
        self.layout.addWidget(self.widget_passo1)

        self.widget_passo2 = QWidget()
        self.layout_grade = QGridLayout(self.widget_passo2)
        self.layout.addWidget(self.widget_passo2)
        self.widget_passo2.hide()

        self.caixa_botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botao_proximo = QPushButton("Gerar Tabela")
        self.caixa_botoes.addButton(self.botao_proximo, QDialogButtonBox.ActionRole)
        self.layout.addWidget(self.caixa_botoes)
        self.caixa_botoes.button(QDialogButtonBox.Ok).setEnabled(False)

        self.botao_proximo.clicked.connect(self.criar_grade_matriz)
        self.caixa_botoes.accepted.connect(self.accept)
        self.caixa_botoes.rejected.connect(self.reject)
        self.entradas_matriz = []
        self.rotulos = []

    def criar_grade_matriz(self):
        for i in reversed(range(self.layout_grade.count())):
            self.layout_grade.itemAt(i).widget().setParent(None)

        num_nos = self.spinbox_nos.value()
        self.rotulos = [chr(ord('A') + i) for i in range(num_nos)]
        self.entradas_matriz = [[None] * num_nos for _ in range(num_nos)]

        for j, rotulo in enumerate(self.rotulos):
            self.layout_grade.addWidget(QLabel(f"<b>{rotulo}</b>"), 0, j + 1, Qt.AlignCenter)

        for i, rotulo in enumerate(self.rotulos):
            self.layout_grade.addWidget(QLabel(f"<b>{rotulo}</b>"), i + 1, 0)
            for j in range(num_nos):
                entrada_linha = QLineEdit("0")
                entrada_linha.setFixedWidth(40)
                entrada_linha.setAlignment(Qt.AlignCenter)

                if i == j:
                    entrada_linha.setDisabled(True)
                elif not self.e_direcionada:
                    if j < i:
                        entrada_linha.setDisabled(True)
                    else:
                        entrada_linha.textChanged.connect(
                            lambda text, r=i, c=j: self.atualizar_valor_simetrico(text, r, c)
                        )
                self.layout_grade.addWidget(entrada_linha, i + 1, j + 1)
                self.entradas_matriz[i][j] = entrada_linha

        self.widget_passo1.hide()
        self.botao_proximo.hide()
        self.widget_passo2.show()
        self.caixa_botoes.button(QDialogButtonBox.Ok).setEnabled(True)
        self.adjustSize()

    def atualizar_valor_simetrico(self, texto, linha, coluna):
        if self.entradas_matriz[coluna][linha]:
            self.entradas_matriz[coluna][linha].setText(texto)

    def obter_dados_matriz(self):
        num_nos = len(self.rotulos)
        matriz = [[0] * num_nos for _ in range(num_nos)]
        for i in range(num_nos):
            for j in range(num_nos):
                try:
                    matriz[i][j] = int(self.entradas_matriz[i][j].text())
                except (ValueError, TypeError):
                    matriz[i][j] = 0
        return self.rotulos, matriz


class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Projeto Grafos")
        self.setStyleSheet(POLISHED_STYLESHEET)
        self.setMinimumSize(1200, 800)

        self.e_direcionada = False

        self.widget_central = QWidget()
        self.setCentralWidget(self.widget_central)
        layout_principal = QHBoxLayout(self.widget_central)
        layout_principal.setContentsMargins(15, 15, 15, 15)
        layout_principal.setSpacing(15)

        self.visualizador_grafo = VisualizadorGrafo()
        self.visualizador_grafo.grafoAlterado.connect(self.gerar_matriz_da_visualizacao)
        layout_principal.addWidget(self.visualizador_grafo, stretch=3)

        painel_controles = QFrame()
        painel_controles.setObjectName("ControlPanel")
        painel_controles.setFixedWidth(380)
        layout_controles = QVBoxLayout(painel_controles)
        layout_controles.setContentsMargins(15, 15, 15, 15)

        layout_controles.addWidget(self.create_title_label("Matriz de Adjacência"))
        self.entrada_matriz_adj = QTextEdit()
        layout_controles.addWidget(self.entrada_matriz_adj, stretch=2)

        layout_controles.addWidget(self.create_title_label("Tipo de Grafo"))
        self.combo_tipo_grafo = QComboBox()
        self.combo_tipo_grafo.addItems(["Não-Orientado", "Orientado"])
        layout_controles.addWidget(self.combo_tipo_grafo)

        layout_controles.addWidget(self.create_title_label("Parâmetros do Caminho"))
        layout_caminho = QHBoxLayout()
        self.entrada_origem = QLineEdit()
        self.entrada_origem.setPlaceholderText("Origem (ex: A)")
        self.entrada_destino = QLineEdit()
        self.entrada_destino.setPlaceholderText("Destino (ex: D)")
        layout_caminho.addWidget(self.entrada_origem)
        layout_caminho.addWidget(self.entrada_destino)
        layout_controles.addLayout(layout_caminho)

        layout_controles.addWidget(self.create_title_label("Modos de Edição"))

        layout_modos = QGridLayout()
        layout_modos.setSpacing(10)
        self.botao_adicionar_nos = QPushButton("Adicionar Nó")
        self.botao_adicionar_nos.setCheckable(True)
        self.botao_editar_no = QPushButton("Editar Rótulo")
        self.botao_editar_no.setCheckable(True)
        self.botao_editar_pesos = QPushButton("Editar Peso")
        self.botao_editar_pesos.setCheckable(True)
        self.botao_deletar_item = QPushButton("Excluir Item")
        self.botao_deletar_item.setCheckable(True)

        self.botoes_modo = [self.botao_adicionar_nos, self.botao_editar_no, self.botao_editar_pesos,
                            self.botao_deletar_item]

        layout_modos.addWidget(self.botao_adicionar_nos, 0, 0)
        layout_modos.addWidget(self.botao_editar_no, 0, 1)
        layout_modos.addWidget(self.botao_editar_pesos, 1, 0)
        layout_modos.addWidget(self.botao_deletar_item, 1, 1)
        layout_controles.addLayout(layout_modos)

        layout_controles.addWidget(self.create_title_label("Ações"))
        grade_acoes = QGridLayout()
        grade_acoes.setSpacing(10)
        self.botao_calcular_rotas = QPushButton("Calcular Rotas")
        self.botao_gerar_matriz = QPushButton("Gerar Matriz do Grafo")
        self.botao_criar_matriz = QPushButton("Criar Matriz por Tabela")
        self.botao_grafo_aleatorio = QPushButton("Grafo Aleatório")
        self.botao_deletar_grafo = QPushButton("Limpar Tudo")
        self.botao_salvar_grafo = QPushButton("Salvar Grafo (TXT)")
        grade_acoes.addWidget(self.botao_calcular_rotas, 0, 0)
        grade_acoes.addWidget(self.botao_gerar_matriz, 0, 1)
        grade_acoes.addWidget(self.botao_criar_matriz, 1, 0)
        grade_acoes.addWidget(self.botao_grafo_aleatorio, 1, 1)
        grade_acoes.addWidget(self.botao_deletar_grafo, 2, 0)
        grade_acoes.addWidget(self.botao_salvar_grafo, 2, 1)
        layout_controles.addLayout(grade_acoes)

        layout_controles.addWidget(self.create_separator())
        layout_controles.addWidget(self.create_title_label("Resultados"))
        self.saida_rotas = QTextEdit()
        self.saida_rotas.setReadOnly(True)
        layout_controles.addWidget(self.saida_rotas, stretch=3)

        layout_principal.addWidget(painel_controles, stretch=1)

        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Pronto.")

        self.combo_tipo_grafo.currentIndexChanged.connect(self.ao_tipo_grafo_alterado)
        for botao in self.botoes_modo:
            botao.clicked.connect(self.ao_botao_modo_alternado)

        self.botao_calcular_rotas.clicked.connect(self.calcular_rotas)
        self.botao_gerar_matriz.clicked.connect(self.gerar_matriz_da_visualizacao)
        self.botao_criar_matriz.clicked.connect(self.criar_matriz_do_input)
        self.botao_grafo_aleatorio.clicked.connect(self.gerar_grafo_aleatorio)
        self.botao_deletar_grafo.clicked.connect(self.deletar_grafo)
        self.botao_salvar_grafo.clicked.connect(self.salvar_dados_grafo_em_txt)

    def ao_botao_modo_alternado(self):
        remetente = self.sender()
        esta_ativo = remetente.isChecked()

        # Desativa todos os modos no backend
        self.visualizador_grafo.definir_modo_adicionar_nos(False)
        self.visualizador_grafo.definir_modo_editar_nos(False)
        self.visualizador_grafo.definir_modo_editar_pesos(False)
        self.visualizador_grafo.definir_modo_deletar(False)

        # Desmarca todos os outros botões
        for botao in self.botoes_modo:
            if botao is not remetente:
                botao.setChecked(False)

        # Ativa o modo correto se o botão foi ativado
        if esta_ativo:
            if remetente == self.botao_adicionar_nos:
                self.visualizador_grafo.definir_modo_adicionar_nos(True)
            elif remetente == self.botao_editar_no:
                self.visualizador_grafo.definir_modo_editar_nos(True)
            elif remetente == self.botao_editar_pesos:
                self.visualizador_grafo.definir_modo_editar_pesos(True)
            elif remetente == self.botao_deletar_item:
                self.visualizador_grafo.definir_modo_deletar(True)

    def ao_tipo_grafo_alterado(self, indice):
        e_novo_modo_direcionado = (indice == 1)
        if e_novo_modo_direcionado == self.e_direcionada:
            return

        resposta = QMessageBox.question(self, 'Mudar Tipo de Grafo',
                                        "Mudar o tipo de grafo irá limpar o cenário atual. Deseja continuar?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if resposta == QMessageBox.Yes:
            self.e_direcionada = e_novo_modo_direcionado
            self.visualizador_grafo.definir_tipo_grafo(self.e_direcionada)
            self.deletar_grafo()
            self.statusBar().showMessage(
                f"Modo alterado para Grafo {'Orientado' if self.e_direcionada else 'Não-Orientado'}.", 5000)
        else:
            self.combo_tipo_grafo.blockSignals(True)
            self.combo_tipo_grafo.setCurrentIndex(0 if not self.e_direcionada else 1)
            self.combo_tipo_grafo.blockSignals(False)

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

    def criar_matriz_do_input(self):
        dialogo = DialogoEntradaMatriz(self.e_direcionada, self)
        if dialogo.exec_() == QDialog.Accepted:
            rotulos, matriz = dialogo.obter_dados_matriz()
            self.visualizador_grafo.limpar()
            self.saida_rotas.clear()
            self.visualizador_grafo.atualizar_da_matriz(rotulos, matriz)
            self.atualizar_texto_matriz_adj(rotulos, matriz)
            self.statusBar().showMessage("Matriz criada e grafo atualizado.", 4000)

    def atualizar_texto_matriz_adj(self, rotulos, mat):
        if not rotulos:
            self.entrada_matriz_adj.setPlainText("Nenhum nó presente para gerar a matriz.")
            return
        cabeçalho = f"    {' '.join(f'{rotulo:^3}' for rotulo in rotulos)}"
        separador = f"  {'-' * (len(cabeçalho) - 2)}"
        string_matriz = [cabeçalho, separador]
        for i, rotulo_linha in enumerate(rotulos):
            valores_linha = " ".join(f"{val:^3}" for val in mat[i])
            string_matriz.append(f"{rotulo_linha:^3}| {valores_linha}")
        self.entrada_matriz_adj.setPlainText("\n".join(string_matriz))

    def gerar_grafo_aleatorio(self):
        try:
            self.visualizador_grafo.limpar()
            n_nos = random.randint(5, 8)
            self.visualizador_grafo.gerar_nos_aleatorios(n_nos)
            self.gerar_matriz_da_visualizacao()
            self.saida_rotas.clear()
            self.statusBar().showMessage(f"{n_nos} nós gerados aleatoriamente.", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar grafo aleatório: {e}")

    def gerar_matriz_da_visualizacao(self):
        try:
            rotulos, mat = self.visualizador_grafo.gerar_matriz_adjacencia()
            self.atualizar_texto_matriz_adj(rotulos, mat)
            if rotulos:
                self.statusBar().showMessage("Matriz gerada a partir da visualização.", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar matriz: {e}")

    def deletar_grafo(self):
        self.visualizador_grafo.limpar()
        self.entrada_matriz_adj.clear()
        self.saida_rotas.clear()
        self.entrada_origem.clear()
        self.entrada_destino.clear()
        self.statusBar().showMessage("Cenário limpo.", 4000)

    def salvar_dados_grafo_em_txt(self):
        rotulos, matriz = self.visualizador_grafo.gerar_matriz_adjacencia()
        conteudo_rotas = self.saida_rotas.toPlainText()
        if not rotulos and not conteudo_rotas.strip():
            QMessageBox.warning(self, "Aviso", "Não há dados de grafo ou resultados para salvar.")
            return
        nome_arquivo, _ = QFileDialog.getSaveFileName(self, "Salvar Dados do Grafo", "dados_grafo.txt",
                                                      "Arquivos de Texto (*.txt);;Todos os Arquivos (*)")
        if nome_arquivo:
            try:
                with open(nome_arquivo, 'w', encoding='utf-8') as arquivo:
                    arquivo.write(
                        f"========== MATRIZ DE ADJACÊNCIA (Grafo {'Orientado' if self.e_direcionada else 'Não-Orientado'}) ==========\n")
                    if rotulos:
                        linha_cabecalho = "    " + "  ".join(f"{rotulo:^3}" for rotulo in rotulos) + "\n"
                        arquivo.write(linha_cabecalho)
                        arquivo.write("-" * (len(linha_cabecalho) + 1) + "\n")
                        for i, rotulo_linha in enumerate(rotulos):
                            valores_linha = " ".join(f"{val:^3}" for val in matriz[i])
                            arquivo.write(f"{rotulo_linha:^3} | {valores_linha}\n")
                    else:
                        arquivo.write("Nenhum nó para gerar a matriz.\n")
                    arquivo.write("\n\n========== RESULTADOS DAS ROTAS ==========\n")
                    arquivo.write(conteudo_rotas if conteudo_rotas.strip() else "Nenhum resultado de rota calculado.\n")
                self.statusBar().showMessage(f"Dados salvos em: {nome_arquivo}", 5000)
                QMessageBox.information(self, "Salvar Grafo", f"Dados salvos com sucesso em:\n{nome_arquivo}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar os dados: {e}")

    def obter_passos_caminho_str(self, G, caminho):
        """Helper para gerar a string de passos detalhados para um caminho."""
        if len(caminho) < 2:
            return ""
        passos = []
        for i in range(len(caminho) - 1):
            u, v = caminho[i], caminho[i + 1]
            custo_aresta = G[u][v]['weight']
            passos.append(f"{u}→{v}: {custo_aresta}")
        return f" <span style='color: #A3BE8C; font-size: 13px;'>({', '.join(passos)})</span>"

    def calcular_rotas(self):
        rotulos, matriz = self.visualizador_grafo.gerar_matriz_adjacencia()
        if not rotulos:
            QMessageBox.warning(self, "Aviso", "O grafo está vazio. Adicione nós e arestas primeiro.")
            return
        origem = self.entrada_origem.text().strip().upper()
        destino = self.entrada_destino.text().strip().upper()
        if not origem or not destino:
            QMessageBox.warning(self, "Aviso", "Origem e destino devem ser preenchidos.")
            return
        if origem not in rotulos or destino not in rotulos:
            QMessageBox.warning(self, "Aviso", f"Nós inválidos. Disponíveis: {', '.join(rotulos)}")
            return
        try:
            G = construir_grafo_nx_da_matriz(rotulos, matriz, self.e_direcionada)
            estilo = "color: #ECEFF4; font-family: 'Segoe UI', sans-serif; font-size: 14px; line-height: 1.6;"
            html = f"<div style='{estilo}'>"
            html += f"<h4>■ Análise de Rotas: {origem} → {destino} ■</h4>"
            todas_rotas = obter_todas_rotas(G, origem, destino, max_nos=10)

            if not todas_rotas:
                html += "<p>Nenhuma rota encontrada.</p>"
            else:
                html += "<p><b>Todas as Rotas Simples:</b></p><ul>"
                rotas_com_custo = []
                for r_path in todas_rotas:
                    custo = nx.path_weight(G, r_path, 'weight')
                    rotas_com_custo.append((r_path, custo))

                rotas_com_custo.sort(key=lambda x: (x[1], len(x[0])))  # Ordena por custo, depois por tamanho

                for r_path, custo in rotas_com_custo:
                    string_caminho = ' → '.join(r_path)
                    string_passos = self.obter_passos_caminho_str(G, r_path)
                    html += f"<li>{string_caminho} &nbsp; (Custo Total: <b>{custo}</b>){string_passos}</li>"
                html += "</ul><br>"

            if caminho_mais_curto := obter_caminho_mais_curto(G, origem, destino):
                custo = nx.path_weight(G, caminho_mais_curto, 'weight')
                string_caminho = ' → '.join(caminho_mais_curto)
                string_passos = self.obter_passos_caminho_str(G, caminho_mais_curto)
                html += f"<p><b>🏆 Rota Mais Curta (menor custo):</b><br> &nbsp; &nbsp; {string_caminho} &nbsp; (Custo: <b>{custo}</b>){string_passos}</p>"

            if caminho_mais_longo := obter_caminho_mais_longo_seguro(G, origem, destino, todas_rotas):
                custo = nx.path_weight(G, caminho_mais_longo, 'weight')
                string_caminho = ' → '.join(caminho_mais_longo)
                string_passos = self.obter_passos_caminho_str(G, caminho_mais_longo)
                html += f"<p><b>🧗 Rota Mais Longa Simples:</b><br> &nbsp; &nbsp; {string_caminho} &nbsp; (Custo: <b>{custo}</b>){string_passos}</p>"

            html += "</div>"
            self.saida_rotas.setHtml(html)
            self.statusBar().showMessage(f"Rotas de {origem} a {destino} calculadas.", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro fatal ao processar grafo: {e}")