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
    obter_caminho_mais_longo_seguro  # Importa classes e funções do módulo 'grafo'.

# =================================================================================
#  FOLHA DE ESTILOS (QSS)
# =================================================================================
# Definição de uma folha de estilos CSS para customizar a aparência da interface.
POLISHED_STYLESHEET = """
QWidget {
    background-color: #2E3440; /* Cor de fundo padrão para todos os widgets */
    color: #ECEFF4; /* Cor do texto padrão */
    font-family: 'Segoe UI', sans-serif; /* Fonte padrão */
    font-size: 14px; /* Tamanho da fonte padrão */
}
#ControlPanel {
    background-color: #3B4252; /* Cor de fundo específica para o painel de controles */
    border-radius: 8px; /* Borda arredondada */
}
#TitleLabel {
    color: #88C0D0; /* Cor do título */
    font-size: 16px; /* Tamanho da fonte do título */
    font-weight: bold; /* Negrito */
    padding-left: 5px; /* Preenchimento à esquerda */
    padding-top: 5px; /* Preenchimento superior */
}
QLineEdit, QTextEdit, QComboBox {
    background-color: #2E3440; /* Cor de fundo para campos de texto e combobox */
    border: 1px solid #4C566A; /* Borda */
    border-radius: 8px; /* Borda arredondada */
    padding: 8px; /* Preenchimento interno */
    transition: border 0.2s ease-in-out; /* Transição suave para a borda */
}
QComboBox::drop-down {
    border: none; /* Remove a borda do botão de dropdown do combobox */
}
QComboBox::down-arrow {
    image: url(:/icons/down-arrow.png); /* Define uma imagem para a seta do dropdown */
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #88C0D0; /* Borda quando o widget está em foco */
}
QPushButton {
    background-color: #5E81AC; /* Cor de fundo padrão para botões */
    color: #ECEFF4; /* Cor do texto do botão */
    font-weight: bold; /* Negrito */
    border: none; /* Sem borda */
    border-radius: 8px; /* Borda arredondada */
    padding: 8px; /* Preenchimento interno */
    min-height: 20px; /* Altura mínima */
    transition: background-color 0.2s ease-in-out; /* Transição suave para a cor de fundo */
}
QPushButton:hover {
    background-color: #81A1C1; /* Cor de fundo ao passar o mouse */
}
QPushButton:pressed {
    background-color: #8FBCBB; /* Cor de fundo ao pressionar o botão */
}
QPushButton:checked {
    background-color: #88C0D0; /* Cor de fundo quando o botão está marcado (toggle) */
    color: #2E3440; /* Cor do texto quando o botão está marcado */
    border: 1px solid #ECEFF4; /* Borda quando o botão está marcado */
}
QStatusBar {
    font-size: 13px; /* Tamanho da fonte da barra de status */
    color: #D8DEE9; /* Cor do texto da barra de status */
}
QStatusBar::item {
    border: none; /* Remove a borda dos itens da barra de status */
}
"""


# =================================================================================
#  JANELA DE DIÁLOGO PARA CRIAÇÃO DA MATRIZ
# =================================================================================

class DialogoEntradaMatriz(QDialog):
    """
    Diálogo para permitir ao usuário inserir os dados para criar uma matriz de adjacência,
    que será usada para gerar o grafo.
    """

    def __init__(self, e_direcionada=False, parent=None):
        super().__init__(parent)
        self.e_direcionada = e_direcionada  # Indica se o grafo a ser criado é direcionado.
        # Define o título do diálogo com base no tipo de grafo.
        titulo = "Criar Matriz (Orientado)" if e_direcionada else "Criar Matriz (Não-Orientado)"
        self.setWindowTitle(titulo)
        self.setMinimumWidth(350)  # Largura mínima do diálogo.

        self.layout = QVBoxLayout(self)  # Layout principal do diálogo.

        # Widget para o primeiro passo: definir o número de nós.
        self.widget_passo1 = QWidget()
        layout_passo1 = QFormLayout(self.widget_passo1)
        self.spinbox_nos = QSpinBox()  # SpinBox para selecionar o número de nós.
        self.spinbox_nos.setRange(2, 26)  # Permite de 2 a 26 nós (letras A-Z).
        self.spinbox_nos.setValue(4)  # Valor inicial.
        layout_passo1.addRow("Número de Nós:", self.spinbox_nos)  # Adiciona ao layout do passo 1.
        self.layout.addWidget(self.widget_passo1)

        # Widget para o segundo passo: a grade da matriz de adjacência.
        self.widget_passo2 = QWidget()
        self.layout_grade = QGridLayout(self.widget_passo2)  # Layout de grade para a matriz.
        self.layout.addWidget(self.widget_passo2)
        self.widget_passo2.hide()  # Esconde inicialmente o passo 2.

        # Botões padrão (OK e Cancelar) e um botão "Gerar Tabela".
        self.caixa_botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botao_proximo = QPushButton("Gerar Tabela")
        self.caixa_botoes.addButton(self.botao_proximo, QDialogButtonBox.ActionRole)
        self.layout.addWidget(self.caixa_botoes)
        self.caixa_botoes.button(QDialogButtonBox.Ok).setEnabled(False)  # Botão OK desabilitado inicialmente.

        # Conexão de sinais e slots.
        self.botao_proximo.clicked.connect(self.criar_grade_matriz)  # Ao clicar em "Gerar Tabela".
        self.caixa_botoes.accepted.connect(self.accept)  # Ao clicar em OK.
        self.caixa_botoes.rejected.connect(self.reject)  # Ao clicar em Cancelar.

        self.entradas_matriz = []  # Lista para armazenar os QLineEdit da matriz.
        self.rotulos = []  # Lista para armazenar os rótulos dos nós.

    def criar_grade_matriz(self):
        """
        Cria dinamicamente a grade de QLineEdit para a matriz de adjacência
        com base no número de nós selecionado.
        """
        # Limpa o layout da grade caso já existam widgets.
        for i in reversed(range(self.layout_grade.count())):
            self.layout_grade.itemAt(i).widget().setParent(None)

        num_nos = self.spinbox_nos.value()  # Obtém o número de nós.
        self.rotulos = [chr(ord('A') + i) for i in range(num_nos)]  # Gera rótulos (A, B, C...).
        self.entradas_matriz = [[None] * num_nos for _ in range(num_nos)]  # Inicializa a lista de QLineEdit.

        # Adiciona rótulos de coluna (A, B, C...) na primeira linha da grade.
        for j, rotulo in enumerate(self.rotulos):
            self.layout_grade.addWidget(QLabel(f"<b>{rotulo}</b>"), 0, j + 1, Qt.AlignCenter)

        # Preenche a grade com QLineEdit para os valores da matriz.
        for i, rotulo in enumerate(self.rotulos):
            self.layout_grade.addWidget(QLabel(f"<b>{rotulo}</b>"), i + 1, 0)  # Adiciona rótulos de linha.
            for j in range(num_nos):
                entrada_linha = QLineEdit("0")  # Campo de entrada com valor inicial "0".
                entrada_linha.setFixedWidth(40)  # Largura fixa.
                entrada_linha.setAlignment(Qt.AlignCenter)  # Alinhamento do texto.

                if i == j:  # Diagonal principal (conexão de um nó consigo mesmo).
                    entrada_linha.setDisabled(True)  # Desabilita a edição.
                elif not self.e_direcionada:
                    if j < i:  # Para grafos não direcionados, a parte inferior triangular é simétrica.
                        entrada_linha.setDisabled(True)  # Desabilita a edição.
                    else:
                        # Conecta o sinal textChanged para atualizar o valor simétrico na matriz.
                        entrada_linha.textChanged.connect(
                            lambda text, r=i, c=j: self.atualizar_valor_simetrico(text, r, c)
                        )
                self.layout_grade.addWidget(entrada_linha, i + 1, j + 1)  # Adiciona o QLineEdit à grade.
                self.entradas_matriz[i][j] = entrada_linha  # Armazena a referência ao QLineEdit.

        self.widget_passo1.hide()  # Esconde o primeiro passo.
        self.botao_proximo.hide()  # Esconde o botão "Gerar Tabela".
        self.widget_passo2.show()  # Mostra o segundo passo (a matriz).
        self.caixa_botoes.button(QDialogButtonBox.Ok).setEnabled(True)  # Habilita o botão OK.
        self.adjustSize()  # Ajusta o tamanho do diálogo para o novo conteúdo.

    def atualizar_valor_simetrico(self, texto, linha, coluna):
        """
        Para grafos não direcionados, mantém a simetria da matriz
        atualizando o valor correspondente.
        """
        if self.entradas_matriz[coluna][linha]:
            # Se o QLineEdit simétrico existe, atualiza seu texto.
            self.entradas_matriz[coluna][linha].setText(texto)

    def obter_dados_matriz(self):
        """Obtém os rótulos e a matriz de adjacência dos QLineEdit preenchidos."""
        num_nos = len(self.rotulos)
        matriz = [[0] * num_nos for _ in range(num_nos)]
        for i in range(num_nos):
            for j in range(num_nos):
                try:
                    # Converte o texto de cada QLineEdit para um inteiro.
                    matriz[i][j] = int(self.entradas_matriz[i][j].text())
                except (ValueError, TypeError):
                    matriz[i][j] = 0  # Se houver erro de conversão, assume 0.
        return self.rotulos, matriz  # Retorna os rótulos e a matriz.


class JanelaPrincipal(QMainWindow):
    """
    Classe principal da aplicação que gerencia a interface gráfica
    e a interação com o visualizador de grafos.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Projeto Grafos")  # Título da janela principal.
        self.setStyleSheet(POLISHED_STYLESHEET)  # Aplica a folha de estilos.
        self.setMinimumSize(1200, 800)  # Tamanho mínimo da janela.

        self.e_direcionada = False  # Flag para o tipo de grafo (inicialmente não direcionado).

        self.widget_central = QWidget()  # Widget central da janela.
        self.setCentralWidget(self.widget_central)
        layout_principal = QHBoxLayout(self.widget_central)  # Layout horizontal principal.
        layout_principal.setContentsMargins(15, 15, 15, 15)  # Margens.
        layout_principal.setSpacing(15)  # Espaçamento entre widgets.

        self.visualizador_grafo = VisualizadorGrafo()  # Instância do visualizador de grafo.
        # Conecta o sinal grafoAlterado do visualizador para atualizar a matriz de adjacência.
        self.visualizador_grafo.grafoAlterado.connect(self.gerar_matriz_da_visualizacao)
        layout_principal.addWidget(self.visualizador_grafo, stretch=3)  # Adiciona o visualizador ao layout.

        painel_controles = QFrame()  # Painel lateral para os controles.
        painel_controles.setObjectName("ControlPanel")  # Nome do objeto para estilização CSS.
        painel_controles.setFixedWidth(380)  # Largura fixa.
        layout_controles = QVBoxLayout(painel_controles)  # Layout vertical para o painel de controles.
        layout_controles.setContentsMargins(15, 15, 15, 15)

        # Seções do painel de controles:

        # 1. Matriz de Adjacência
        layout_controles.addWidget(self.create_title_label("Matriz de Adjacência"))
        self.entrada_matriz_adj = QTextEdit()  # Campo para exibir a matriz de adjacência.
        layout_controles.addWidget(self.entrada_matriz_adj, stretch=2)

        # 2. Tipo de Grafo
        layout_controles.addWidget(self.create_title_label("Tipo de Grafo"))
        self.combo_tipo_grafo = QComboBox()  # ComboBox para selecionar o tipo de grafo.
        self.combo_tipo_grafo.addItems(["Não-Orientado", "Orientado"])
        layout_controles.addWidget(self.combo_tipo_grafo)

        # 3. Parâmetros do Caminho (Origem e Destino para cálculo de rotas)
        layout_controles.addWidget(self.create_title_label("Parâmetros do Caminho"))
        layout_caminho = QHBoxLayout()  # Layout horizontal para os campos de origem e destino.
        self.entrada_origem = QLineEdit()  # Campo para a origem.
        self.entrada_origem.setPlaceholderText("Origem (ex: A)")
        self.entrada_destino = QLineEdit()  # Campo para o destino.
        self.entrada_destino.setPlaceholderText("Destino (ex: D)")
        layout_caminho.addWidget(self.entrada_origem)
        layout_caminho.addWidget(self.entrada_destino)
        layout_controles.addLayout(layout_caminho)

        # 4. Modos de Edição (Botões de alternância)
        layout_controles.addWidget(self.create_title_label("Modos de Edição"))
        layout_modos = QGridLayout()  # Layout de grade para os botões de modo.
        layout_modos.setSpacing(10)
        self.botao_adicionar_nos = QPushButton("Adicionar Nó")
        self.botao_adicionar_nos.setCheckable(True)  # Botão de alternância.
        self.botao_editar_no = QPushButton("Editar Rótulo")
        self.botao_editar_no.setCheckable(True)
        self.botao_editar_pesos = QPushButton("Editar Peso")
        self.botao_editar_pesos.setCheckable(True)
        self.botao_deletar_item = QPushButton("Excluir Item")
        self.botao_deletar_item.setCheckable(True)

        self.botoes_modo = [self.botao_adicionar_nos, self.botao_editar_no, self.botao_editar_pesos,
                            self.botao_deletar_item]  # Lista de botões de modo.

        # Adiciona os botões de modo ao layout de grade.
        layout_modos.addWidget(self.botao_adicionar_nos, 0, 0)
        layout_modos.addWidget(self.botao_editar_no, 0, 1)
        layout_modos.addWidget(self.botao_editar_pesos, 1, 0)
        layout_modos.addWidget(self.botao_deletar_item, 1, 1)
        layout_controles.addLayout(layout_modos)

        # 5. Ações (Botões de funcionalidade)
        layout_controles.addWidget(self.create_title_label("Ações"))
        grade_acoes = QGridLayout()  # Layout de grade para os botões de ação.
        grade_acoes.setSpacing(10)
        self.botao_calcular_rotas = QPushButton("Calcular Rotas")
        self.botao_gerar_matriz = QPushButton("Gerar Matriz do Grafo")
        self.botao_criar_matriz = QPushButton("Criar Matriz por Tabela")
        self.botao_grafo_aleatorio = QPushButton("Grafo Aleatório")
        self.botao_deletar_grafo = QPushButton("Limpar Tudo")
        self.botao_salvar_grafo = QPushButton("Salvar Grafo (TXT)")

        # Adiciona os botões de ação ao layout de grade.
        grade_acoes.addWidget(self.botao_calcular_rotas, 0, 0)
        grade_acoes.addWidget(self.botao_gerar_matriz, 0, 1)
        grade_acoes.addWidget(self.botao_criar_matriz, 1, 0)
        grade_acoes.addWidget(self.botao_grafo_aleatorio, 1, 1)
        grade_acoes.addWidget(self.botao_deletar_grafo, 2, 0)
        grade_acoes.addWidget(self.botao_salvar_grafo, 2, 1)
        layout_controles.addLayout(grade_acoes)

        # Separador visual.
        layout_controles.addWidget(self.create_separator())

        # 6. Resultados (Saída das rotas)
        layout_controles.addWidget(self.create_title_label("Resultados"))
        self.saida_rotas = QTextEdit()  # Campo para exibir os resultados das rotas.
        self.saida_rotas.setReadOnly(True)  # Apenas leitura.
        layout_controles.addWidget(self.saida_rotas, stretch=3)

        layout_principal.addWidget(painel_controles, stretch=1)  # Adiciona o painel de controles ao layout principal.

        self.setStatusBar(QStatusBar(self))  # Cria uma barra de status.
        self.statusBar().showMessage("Pronto.")  # Mensagem inicial na barra de status.

        # Conexões de sinais e slots para os controles.
        self.combo_tipo_grafo.currentIndexChanged.connect(self.ao_tipo_grafo_alterado)  # Ao mudar o tipo de grafo.
        for botao in self.botoes_modo:
            botao.clicked.connect(self.ao_botao_modo_alternado)  # Ao clicar em um botão de modo.

        self.botao_calcular_rotas.clicked.connect(self.calcular_rotas)  # Ao clicar em "Calcular Rotas".
        self.botao_gerar_matriz.clicked.connect(self.gerar_matriz_da_visualizacao)  # Ao clicar em "Gerar Matriz".
        self.botao_criar_matriz.clicked.connect(self.criar_matriz_do_input)  # Ao clicar em "Criar Matriz por Tabela".
        self.botao_grafo_aleatorio.clicked.connect(self.gerar_grafo_aleatorio)  # Ao clicar em "Grafo Aleatório".
        self.botao_deletar_grafo.clicked.connect(self.deletar_grafo)  # Ao clicar em "Limpar Tudo".
        self.botao_salvar_grafo.clicked.connect(self.salvar_dados_grafo_em_txt)  # Ao clicar em "Salvar Grafo".

    def ao_botao_modo_alternado(self):
        """
        Gerencia o comportamento dos botões de modo de edição, garantindo
        que apenas um modo esteja ativo por vez.
        """
        remetente = self.sender()  # Obtém o botão que disparou o evento.
        esta_ativo = remetente.isChecked()  # Verifica se o botão foi marcado (ativado).

        # Desativa todos os modos no backend do visualizador de grafo.
        self.visualizador_grafo.definir_modo_adicionar_nos(False)
        self.visualizador_grafo.definir_modo_editar_nos(False)
        self.visualizador_grafo.definir_modo_editar_pesos(False)
        self.visualizador_grafo.definir_modo_deletar(False)

        # Desmarca visualmente todos os outros botões de modo.
        for botao in self.botoes_modo:
            if botao is not remetente:
                botao.setChecked(False)

        # Ativa o modo correto no visualizador se o botão foi ativado.
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
        """
        Lida com a mudança do tipo de grafo (direcionado/não-direcionado).
        Avisa o usuário que a mudança limpará o grafo atual.
        """
        e_novo_modo_direcionado = (indice == 1)  # True se o novo modo for "Orientado".
        if e_novo_modo_direcionado == self.e_direcionada:
            return  # Não faz nada se o modo não mudou.

        # Exibe uma caixa de diálogo de confirmação.
        resposta = QMessageBox.question(self, 'Mudar Tipo de Grafo',
                                        "Mudar o tipo de grafo irá limpar o cenário atual. Deseja continuar?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if resposta == QMessageBox.Yes:
            self.e_direcionada = e_novo_modo_direcionado  # Atualiza a flag interna.
            self.visualizador_grafo.definir_tipo_grafo(self.e_direcionada)  # Define o tipo no visualizador.
            self.deletar_grafo()  # Limpa o grafo atual.
            self.statusBar().showMessage(  # Atualiza a barra de status.
                f"Modo alterado para Grafo {'Orientado' if self.e_direcionada else 'Não-Orientado'}.", 5000)
        else:
            # Se o usuário cancelar, reverte a seleção no ComboBox para o estado anterior.
            self.combo_tipo_grafo.blockSignals(True)  # Bloqueia sinais para evitar loop infinito.
            self.combo_tipo_grafo.setCurrentIndex(0 if not self.e_direcionada else 1)
            self.combo_tipo_grafo.blockSignals(False)

    def create_title_label(self, text):
        """Cria um QLabel estilizado para títulos de seção."""
        label = QLabel(text)
        label.setObjectName("TitleLabel")  # Define o nome do objeto para estilização CSS.
        return label

    def create_separator(self):
        """Cria um QFrame que funciona como um separador horizontal."""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)  # Forma de linha horizontal.
        line.setFrameShadow(QFrame.Sunken)  # Efeito de sombra.
        line.setFixedHeight(1)  # Altura fixa de 1 pixel.
        line.setObjectName("Separator")  # Nome do objeto para estilização CSS.
        return line

    def criar_matriz_do_input(self):
        """
        Abre o diálogo de entrada da matriz, obtém os dados e atualiza o grafo
        e a visualização da matriz.
        """
        dialogo = DialogoEntradaMatriz(self.e_direcionada, self)  # Instancia o diálogo da matriz.
        if dialogo.exec_() == QDialog.Accepted:  # Se o usuário clicar em OK no diálogo.
            rotulos, matriz = dialogo.obter_dados_matriz()  # Obtém os dados da matriz preenchidos.
            self.visualizador_grafo.limpar()  # Limpa o grafo atual.
            self.saida_rotas.clear()  # Limpa os resultados de rotas.
            self.visualizador_grafo.atualizar_da_matriz(rotulos, matriz)  # Atualiza o grafo visualmente.
            self.atualizar_texto_matriz_adj(rotulos, matriz)  # Atualiza o QTextEdit da matriz.
            self.statusBar().showMessage("Matriz criada e grafo atualizado.", 4000)  # Mensagem na barra de status.

    def atualizar_texto_matriz_adj(self, rotulos, mat):
        """
        Formata e exibe a matriz de adjacência no QTextEdit.
        """
        if not rotulos:
            self.entrada_matriz_adj.setPlainText("Nenhum nó presente para gerar a matriz.")
            return

        # Constrói o cabeçalho da matriz (rótulos das colunas).
        cabeçalho = f"    {' '.join(f'{rotulo:^3}' for rotulo in rotulos)}"
        # Constrói a linha separadora.
        separador = f"  {'-' * (len(cabeçalho) - 2)}"
        string_matriz = [cabeçalho, separador]  # Lista para as linhas da matriz formatada.

        # Adiciona cada linha da matriz com rótulos de linha e valores.
        for i, rotulo_linha in enumerate(rotulos):
            valores_linha = " ".join(f"{val:^3}" for val in mat[i])
            string_matriz.append(f"{rotulo_linha:^3}| {valores_linha}")
        self.entrada_matriz_adj.setPlainText("\n".join(string_matriz))  # Define o texto no QTextEdit.

    def gerar_grafo_aleatorio(self):
        """
        Gera um grafo com um número aleatório de nós e arestas,
        e atualiza a visualização e a matriz.
        """
        try:
            self.visualizador_grafo.limpar()  # Limpa o grafo atual.
            n_nos = random.randint(5, 8)  # Gera entre 5 e 8 nós aleatoriamente.
            self.visualizador_grafo.gerar_nos_aleatorios(n_nos)  # Gera os nós e arestas.
            self.gerar_matriz_da_visualizacao()  # Atualiza a matriz exibida.
            self.saida_rotas.clear()  # Limpa os resultados de rotas.
            self.statusBar().showMessage(f"{n_nos} nós gerados aleatoriamente.", 4000)  # Mensagem na barra de status.
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar grafo aleatório: {e}")  # Exibe erro.

    def gerar_matriz_da_visualizacao(self):
        """
        Gera a matriz de adjacência a partir do grafo atualmente desenhado
        e a exibe no QTextEdit.
        """
        try:
            rotulos, mat = self.visualizador_grafo.gerar_matriz_adjacencia()  # Obtém a matriz do visualizador.
            self.atualizar_texto_matriz_adj(rotulos, mat)  # Atualiza o texto da matriz.
            if rotulos:
                self.statusBar().showMessage("Matriz gerada a partir da visualização.",
                                             4000)  # Mensagem na barra de status.
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar matriz: {e}")  # Exibe erro.

    def deletar_grafo(self):
        """
        Limpa completamente o grafo, a matriz de adjacência,
        os resultados de rotas e os campos de origem/destino.
        """
        self.visualizador_grafo.limpar()  # Limpa o visualizador do grafo.
        self.entrada_matriz_adj.clear()  # Limpa o campo da matriz.
        self.saida_rotas.clear()  # Limpa os resultados de rotas.
        self.entrada_origem.clear()  # Limpa o campo de origem.
        self.entrada_destino.clear()  # Limpa o campo de destino.
        self.statusBar().showMessage("Cenário limpo.", 4000)  # Mensagem na barra de status.

    def salvar_dados_grafo_em_txt(self):
        """
        Salva a matriz de adjacência e os resultados das rotas em um arquivo de texto.
        """
        rotulos, matriz = self.visualizador_grafo.gerar_matriz_adjacencia()  # Obtém a matriz.
        conteudo_rotas = self.saida_rotas.toPlainText()  # Obtém o texto dos resultados de rotas.

        if not rotulos and not conteudo_rotas.strip():
            QMessageBox.warning(self, "Aviso", "Não há dados de grafo ou resultados para salvar.")
            return  # Avisa se não houver nada para salvar.

        # Abre uma caixa de diálogo para o usuário escolher o nome e local do arquivo.
        nome_arquivo, _ = QFileDialog.getSaveFileName(self, "Salvar Dados do Grafo", "dados_grafo.txt",
                                                      "Arquivos de Texto (*.txt);;Todos os Arquivos (*)")
        if nome_arquivo:  # Se o usuário selecionou um arquivo.
            try:
                with open(nome_arquivo, 'w', encoding='utf-8') as arquivo:  # Abre o arquivo para escrita.
                    arquivo.write(  # Escreve o cabeçalho da matriz.
                        f"========== MATRIZ DE ADJACÊNCIA (Grafo {'Orientado' if self.e_direcionada else 'Não-Orientado'}) ==========\n")
                    if rotulos:  # Se houver nós, escreve a matriz formatada.
                        linha_cabecalho = "    " + "  ".join(f"{rotulo:^3}" for rotulo in rotulos) + "\n"
                        arquivo.write(linha_cabecalho)
                        arquivo.write("-" * (len(linha_cabecalho) + 1) + "\n")
                        for i, rotulo_linha in enumerate(rotulos):
                            valores_linha = " ".join(f"{val:^3}" for val in matriz[i])
                            arquivo.write(f"{rotulo_linha:^3} | {valores_linha}\n")
                    else:
                        arquivo.write("Nenhum nó para gerar a matriz.\n")
                    arquivo.write("\n\n========== RESULTADOS DAS ROTAS ==========\n")  # Cabeçalho dos resultados.
                    # Escreve os resultados das rotas ou uma mensagem se não houver.
                    arquivo.write(conteudo_rotas if conteudo_rotas.strip() else "Nenhum resultado de rota calculado.\n")
                self.statusBar().showMessage(f"Dados salvos em: {nome_arquivo}", 5000)  # Mensagem de sucesso.
                QMessageBox.information(self, "Salvar Grafo",
                                        f"Dados salvos com sucesso em:\n{nome_arquivo}")  # Confirmação.
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar os dados: {e}")  # Exibe erro ao salvar.

    def obter_passos_caminho_str(self, G, caminho):
        """
        Função auxiliar para gerar uma string formatada com os passos e custos
        individuais de um caminho.
        """
        if len(caminho) < 2:
            return ""  # Caminho muito curto, sem passos.
        passos = []
        for i in range(len(caminho) - 1):
            u, v = caminho[i], caminho[i + 1]
            custo_aresta = G[u][v]['weight']  # Obtém o peso da aresta.
            passos.append(f"{u}→{v}: {custo_aresta}")  # Formata o passo.
        return f" <span style='color: #A3BE8C; font-size: 13px;'>({', '.join(passos)})</span>"

    def calcular_rotas(self):
        """
        Calcula e exibe as rotas (todas as simples, mais curta, mais longa)
        entre os nós de origem e destino especificados.
        """
        rotulos, matriz = self.visualizador_grafo.gerar_matriz_adjacencia()  # Obtém a matriz do grafo.
        if not rotulos:
            QMessageBox.warning(self, "Aviso", "O grafo está vazio. Adicione nós e arestas primeiro.")
            return  # Avisa se o grafo estiver vazio.

        origem = self.entrada_origem.text().strip().upper()  # Obtém e formata o nó de origem.
        destino = self.entrada_destino.text().strip().upper()  # Obtém e formata o nó de destino.

        if not origem or not destino:
            QMessageBox.warning(self, "Aviso", "Origem e destino devem ser preenchidos.")
            return  # Avisa se origem ou destino estiverem vazios.

        if origem not in rotulos or destino not in rotulos:
            QMessageBox.warning(self, "Aviso", f"Nós inválidos. Disponíveis: {', '.join(rotulos)}")
            return  # Avisa se os nós não existirem.

        try:
            G = construir_grafo_nx_da_matriz(rotulos, matriz, self.e_direcionada)  # Constrói o grafo NetworkX.

            # Configura o estilo HTML para a saída de rotas.
            estilo = "color: #ECEFF4; font-family: 'Segoe UI', sans-serif; font-size: 14px; line-height: 1.6;"
            html = f"<div style='{estilo}'>"
            html += f"<h4>■ Análise de Rotas: {origem} → {destino} ■</h4>"

            todas_rotas = obter_todas_rotas(G, origem, destino, max_nos=10)  # Obtém todas as rotas simples.

            if not todas_rotas:
                html += "<p>Nenhuma rota encontrada.</p>"  # Mensagem se não houver rotas.
            else:
                html += "<p><b>Todas as Rotas Simples:</b></p><ul>"
                rotas_com_custo = []
                for r_path in todas_rotas:
                    custo = nx.path_weight(G, r_path, 'weight')  # Calcula o custo de cada rota.
                    rotas_com_custo.append((r_path, custo))

                # Ordena as rotas por custo e depois por tamanho do caminho.
                rotas_com_custo.sort(key=lambda x: (x[1], len(x[0])))

                for r_path, custo in rotas_com_custo:
                    string_caminho = ' → '.join(r_path)  # Formata o caminho.
                    string_passos = self.obter_passos_caminho_str(G, r_path)  # Obtém os passos detalhados.
                    html += f"<li>{string_caminho} &nbsp; (Custo Total: <b>{custo}</b>){string_passos}</li>"
                html += "</ul><br>"

            # Obtém e exibe o caminho mais curto.
            if caminho_mais_curto := obter_caminho_mais_curto(G, origem, destino):
                custo = nx.path_weight(G, caminho_mais_curto, 'weight')
                string_caminho = ' → '.join(caminho_mais_curto)
                string_passos = self.obter_passos_caminho_str(G, caminho_mais_curto)
                html += f"<p><b>🏆 Rota Mais Curta (menor custo):</b><br> &nbsp; &nbsp; {string_caminho} &nbsp; (Custo: <b>{custo}</b>){string_passos}</p>"

            # Obtém e exibe o caminho mais longo (entre as rotas simples encontradas).
            if caminho_mais_longo := obter_caminho_mais_longo_seguro(G, origem, destino, todas_rotas):
                custo = nx.path_weight(G, caminho_mais_longo, 'weight')
                string_caminho = ' → '.join(caminho_mais_longo)
                string_passos = self.obter_passos_caminho_str(G, caminho_mais_longo)
                html += f"<p><b>🧗 Rota Mais Longa Simples:</b><br> &nbsp; &nbsp; {string_caminho} &nbsp; (Custo: <b>{custo}</b>){string_passos}</p>"

            html += "</div>"
            self.saida_rotas.setHtml(html)  # Define o HTML na área de resultados.
            self.statusBar().showMessage(f"Rotas de {origem} a {destino} calculadas.", 4000)  # Mensagem de sucesso.
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro fatal ao processar grafo: {e}")  # Exibe erro fatal.