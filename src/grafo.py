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

class ItemNo(QGraphicsEllipseItem):
    """Representa um nó (vértice) que pode ser arrastado na cena."""

    def __init__(self, rotulo, x, y, raio=20):
        # Construtor da classe base QGraphicsEllipseItem, definindo a forma do nó como uma elipse/círculo.
        super().__init__(-raio, -raio, 2 * raio, 2 * raio)
        self.arestas = []  # Lista para armazenar as arestas conectadas a este nó.
        self.raio = raio    # Raio do nó.

        # Flags que permitem que o item seja móvel (arrastável), selecionável e que envie
        # notificações de mudança de geometria (para as arestas se atualizarem).
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable)
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges)

        # Definição das cores para o preenchimento do nó (normal e selecionado).
        self.pincel_normal = QBrush(QColor("#5E81AC"))
        self.pincel_selecionado = QBrush(QColor("#88C0D0"))
        self.setBrush(self.pincel_normal)  # Define a cor de preenchimento inicial.
        self.setPen(QPen(QColor("#88C0D0"), 2)) # Define a caneta para o contorno do nó.

        # Configuração do efeito de sombra para o nó.
        self.sombra = QGraphicsDropShadowEffect()
        self.sombra.setBlurRadius(15)      # Raio do desfoque da sombra.
        self.sombra.setColor(QColor("#88C0D0")) # Cor da sombra.
        self.sombra.setOffset(QPointF(0, 0)) # Deslocamento da sombra.

        self.setGraphicsEffect(self.sombra) # Aplica o efeito de sombra ao nó.
        self.sombra.setEnabled(False)      # Sombra inicialmente desativada.

        # Cria um item de texto para o rótulo do nó e o associa a este nó como seu pai.
        self.item_texto = QGraphicsTextItem(rotulo, self)
        font = QFont("Segoe UI", 11, QFont.Bold) # Define a fonte do rótulo.
        self.item_texto.setFont(font)
        self.item_texto.setDefaultTextColor(QColor("#ECEFF4")) # Cor do texto.

        self.setPos(x, y) # Define a posição inicial do nó na cena.
        self.rotulo = rotulo # Armazena o rótulo do nó.
        self.definir_rotulo(rotulo) # Chama o método para posicionar corretamente o rótulo.

    def adicionar_aresta(self, aresta):
        """Adiciona uma aresta à lista de arestas conectadas a este nó, se ainda não estiver lá."""
        if aresta not in self.arestas:
            self.arestas.append(aresta)

    def definir_rotulo(self, novo_rotulo):
        """Atualiza o rótulo do nó e centraliza o texto."""
        self.rotulo = novo_rotulo # Atualiza o atributo do rótulo.
        self.item_texto.setPlainText(novo_rotulo) # Atualiza o texto exibido.
        # Centraliza o texto do rótulo dentro do nó.
        self.item_texto.setPos(-self.item_texto.boundingRect().width() / 2, -self.item_texto.boundingRect().height() / 2)

    def itemChange(self, change, value):
        """Método chamado quando uma propriedade do item muda. Usado para atualizar a geometria das arestas."""
        if change == QGraphicsEllipseItem.ItemPositionHasChanged:
            # Se a posição do nó mudou, itera sobre todas as arestas conectadas e as atualiza.
            for aresta in self.arestas:
                aresta.atualizar_geometria()
        return super().itemChange(change, value)

    def definir_selecionado(self, esta_selecionado):
        """Define o estado de seleção do nó, ativando/desativando a sombra e mudando a cor."""
        self.sombra.setEnabled(esta_selecionado) # Ativa ou desativa a sombra.
        self.setBrush(self.pincel_selecionado if esta_selecionado else self.pincel_normal) # Muda a cor de preenchimento.

class ItemAresta(QGraphicsLineItem):
    """Representa uma aresta, com lógica para desenhar linhas retas ou curvas."""

    def __init__(self, no_origem: ItemNo, no_destino: ItemNo, peso: int = 1, e_direcionada=False):
        super().__init__()
        self.no_origem = no_origem     # Nó de origem da aresta.
        self.no_destino = no_destino   # Nó de destino da aresta.
        self.peso = peso               # Peso da aresta.
        self.e_direcionada = e_direcionada # Indica se a aresta é direcionada.
        self.tamanho_seta = 12         # Tamanho da seta (se for direcionada).
        self.e_reciproca = False       # Flag para indicar se há uma aresta recíproca (para desenhar curva).

        self._caminho = QPainterPath() # Objeto QPainterPath para desenhar a linha (pode ser reta ou curva).
        self.setZValue(-1)             # Define o Z-Value para que as arestas fiquem atrás dos nós.
        self.caneta_linha = QPen(QColor("#4C566A"), 2.5) # Define a caneta para desenhar a linha da aresta.
        self.setPen(self.caneta_linha) # Aplica a caneta.

        # Cria um item de texto para exibir o peso da aresta.
        self.item_texto_aresta = QGraphicsTextItem(str(self.peso))
        font = QFont("Segoe UI", 10) # Define a fonte do texto do peso.
        self.item_texto_aresta.setFont(font)
        self.item_texto_aresta.setDefaultTextColor(QColor("#D8DEE9")) # Cor do texto.

        # Adiciona a aresta às listas de arestas dos nós de origem e destino.
        self.no_origem.adicionar_aresta(self)
        self.no_destino.adicionar_aresta(self)
        self.atualizar_geometria() # Atualiza a posição e forma da aresta.

    def adicionar_texto_a_cena(self, cena):
        """Adiciona o item de texto do peso da aresta à cena."""
        cena.addItem(self.item_texto_aresta)

    def definir_peso(self, peso):
        """Define o peso da aresta e atualiza o texto exibido."""
        self.peso = peso
        self.item_texto_aresta.setPlainText(str(self.peso))

    def boundingRect(self):
        """Retorna o retângulo delimitador do item, ajustado para incluir a seta e texto."""
        # O ajuste é para garantir que a área de redesenho seja suficiente.
        return self._caminho.boundingRect().adjusted(-20, -20, 20, 20)

    def shape(self):
        """Retorna a forma exata da aresta para detecção de colisão e eventos de clique."""
        return self._caminho

    def atualizar_geometria(self):
        """Atualiza a posição e forma da aresta com base nas posições dos nós."""
        self.prepareGeometryChange() # Notifica a cena sobre uma mudança iminente na geometria.
        p1 = self.no_origem.pos()  # Posição do nó de origem.
        p2 = self.no_destino.pos() # Posição do nó de destino.

        # Calcula o ângulo da linha entre os centros dos nós.
        angulo_linha_rad = atan2(p2.y() - p1.y(), p2.x() - p1.x())

        # Calcula os pontos de início e fim da linha da aresta, considerando o raio dos nós
        # para que a linha comece e termine na borda dos nós, e não no centro.
        dx_origem = cos(angulo_linha_rad) * self.no_origem.raio
        dy_origem = sin(angulo_linha_rad) * self.no_origem.raio
        ponto_inicial = p1 + QPointF(dx_origem, dy_origem)

        dx_destino = cos(angulo_linha_rad) * self.no_destino.raio
        dy_destino = sin(angulo_linha_rad) * self.no_destino.raio
        ponto_final = p2 - QPointF(dx_destino, dy_destino)

        self._caminho = QPainterPath(ponto_inicial) # Inicia o caminho da aresta.

        if self.e_reciproca:
            # Se houver uma aresta recíproca, desenha uma curva para evitar sobreposição.
            dx, dy = p2.x() - p1.x(), p2.y() - p1.y()
            ponto_meio = (ponto_inicial + ponto_final) / 2 # Ponto médio entre os pontos iniciais e finais da linha.
            perp_dx, perp_dy = -dy, dx # Vetor perpendicular à linha.
            norm = sqrt(perp_dx ** 2 + perp_dy ** 2) # Normaliza o vetor perpendicular.
            perp_dx, perp_dy = (perp_dx / norm, perp_dy / norm) if norm > 0 else (0, 0)

            distancia_deslocamento = 30 # Distância para deslocar o ponto de controle da curva.
            # Inverte o deslocamento para que as duas arestas recíprocas se curvem em direções opostas.
            if self.no_origem.rotulo > self.no_destino.rotulo:
                distancia_deslocamento *= -1

            # Calcula o ponto de controle para a curva de Bézier quadrática.
            ponto_controle = ponto_meio + QPointF(perp_dx * distancia_deslocamento, perp_dy * distancia_deslocamento)
            self._caminho.quadTo(ponto_controle, ponto_final) # Desenha a curva.
        else:
            self._caminho.lineTo(ponto_final) # Desenha uma linha reta.

        # Posiciona o texto do peso da aresta no meio do caminho.
        posicao_texto = self._caminho.pointAtPercent(0.5)
        self.item_texto_aresta.setPos(posicao_texto)
        self.update() # Solicita uma atualização de pintura do item.

    def paint(self, painter, option, widget=None):
        """Método de pintura para desenhar a aresta e a seta (se aplicável)."""
        painter.setRenderHint(QPainter.Antialiasing) # Ativa o antialiasing para um desenho suave.
        painter.setPen(self.caneta_linha)          # Aplica a caneta definida.
        painter.drawPath(self._caminho)            # Desenha o caminho (linha ou curva).

        if self.e_direcionada:
            # Se a aresta for direcionada, desenha uma seta no ponto final.
            painter.setBrush(QBrush(QColor("#88C0D0"))) # Define a cor de preenchimento para a seta.
            angulo_no_fim = self._caminho.angleAtPercent(1) # Obtém o ângulo no final do caminho.
            self.desenhar_seta(painter, self._caminho.pointAtPercent(1), angulo_no_fim) # Desenha a seta.

    def desenhar_seta(self, painter, ponto, angulo_graus):
        """Desenha uma seta triangular em um dado ponto com um determinado ângulo."""
        s = self.tamanho_seta # Tamanho da seta.
        # Define os pontos de um triângulo para formar a cabeça da seta.
        cabeca_seta = QPolygonF([
            QPointF(0, 0),
            QPointF(-s, -s / 2.5),
            QPointF(-s, s / 2.5)
        ])

        # Cria uma transformação para posicionar e rotacionar a seta corretamente.
        transformar = QTransform()
        transformar.translate(ponto.x(), ponto.y()) # Translada para o ponto desejado.
        transformar.rotate(-angulo_graus)           # Rotaciona a seta para alinhar com o ângulo da aresta.
        painter.drawPolygon(transformar.map(cabeca_seta)) # Desenha a seta transformada.

class VisualizadorGrafo(QGraphicsView):
    grafoAlterado = pyqtSignal() # Sinal emitido quando o grafo é alterado (adicionar/deletar nós/arestas, editar).

    def __init__(self):
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing) # Ativa o antialiasing para renderização suave.
        self.cena = QGraphicsScene()              # Cria a cena gráfica onde os itens serão desenhados.
        self.setScene(self.cena)                  # Define a cena para a view.
        self.nos, self.arestas = {}, []           # Dicionário para nós (rótulo: objeto ItemNo) e lista para arestas.
        self.e_direcionada = False                # Flag para indicar se o grafo é direcionado.
        self.setBackgroundBrush(QBrush(QColor("#262b33"))) # Define a cor de fundo da cena.
        self.no_selecionado = None                # Armazena o nó atualmente selecionado.

        # Flags para controlar os diferentes modos de interação do usuário.
        self.modo_adicionar_nos = False
        self.modo_editar_nos = False
        self.modo_editar_pesos = False
        self.modo_deletar = False

    def definir_tipo_grafo(self, e_direcionada: bool):
        """Define se o grafo é direcionado ou não."""
        self.e_direcionada = e_direcionada

    def definir_modo_adicionar_nos(self, ativado: bool):
        """Ativa/desativa o modo de adicionar nós e muda o cursor."""
        self.modo_adicionar_nos = ativado
        self.setCursor(Qt.PointingHandCursor if ativado else Qt.ArrowCursor)

    def definir_modo_editar_nos(self, ativado: bool):
        """Ativa/desativa o modo de editar rótulos de nós e muda o cursor."""
        self.modo_editar_nos = ativado
        self.setCursor(Qt.IBeamCursor if ativado else Qt.ArrowCursor)

    def definir_modo_editar_pesos(self, ativado: bool):
        """Ativa/desativa o modo de editar pesos de arestas e muda o cursor."""
        self.modo_editar_pesos = ativado
        self.setCursor(Qt.IBeamCursor if ativado else Qt.ArrowCursor)

    def definir_modo_deletar(self, ativado: bool):
        """Ativa/desativa o modo de deletar itens e muda o cursor."""
        self.modo_deletar = ativado
        self.setCursor(Qt.CrossCursor if ativado else Qt.ArrowCursor)

    def adicionar_no(self, rotulo, x, y):
        """Adiciona um novo nó à cena e ao dicionário de nós."""
        if rotulo in self.nos: # Evita adicionar nós com rótulos duplicados.
            return
        no = ItemNo(rotulo, x, y) # Cria uma nova instância de ItemNo.
        self.nos[rotulo] = no    # Adiciona o nó ao dicionário.
        self.cena.addItem(no)   # Adiciona o nó à cena gráfica.

    def adicionar_aresta(self, rotulo1, rotulo2, peso):
        """Adiciona uma nova aresta entre dois nós na cena."""
        no1, no2 = self.nos.get(rotulo1), self.nos.get(rotulo2)
        # Verifica se os nós existem e se a aresta já não existe (para evitar duplicatas).
        if not (no1 and no2) or any(e.no_origem == no1 and e.no_destino == no2 for e in self.arestas):
            return

        nova_aresta = ItemAresta(no1, no2, peso, self.e_direcionada) # Cria uma nova instância de ItemAresta.

        if self.e_direcionada:
            # Se o grafo for direcionado, verifica se existe uma aresta oposta
            # para marcar a nova aresta como recíproca (para desenho curvo).
            aresta_oposta = next((e for e in self.arestas if e.no_origem == no2 and e.no_destino == no1), None)
            if aresta_oposta:
                nova_aresta.e_reciproca = True # Marca a nova aresta como recíproca.

        self.arestas.append(nova_aresta)        # Adiciona a nova aresta à lista de arestas.
        self.cena.addItem(nova_aresta)         # Adiciona a aresta à cena gráfica.
        nova_aresta.adicionar_texto_a_cena(self.cena) # Adiciona o texto do peso à cena.
        nova_aresta.atualizar_geometria()       # Atualiza a geometria da aresta.
        self.grafoAlterado.emit()               # Emite o sinal de que o grafo foi alterado.

    def deletar_aresta(self, aresta_para_deletar):
        """Deleta uma aresta da cena e das listas internas."""
        if aresta_para_deletar not in self.arestas: # Verifica se a aresta existe.
            return

        # Verifica se há uma aresta oposta para remover a flag de reciprocidade.
        aresta_oposta = next((e for e in self.arestas if
                              e.no_origem == aresta_para_deletar.no_destino and e.no_destino == aresta_para_deletar.no_origem),
                             None)

        if aresta_para_deletar.scene():
            # Remove a aresta e seu texto associado da cena.
            self.cena.removeItem(aresta_para_deletar.item_texto_aresta)
            self.cena.removeItem(aresta_para_deletar)

        self.arestas.remove(aresta_para_deletar) # Remove a aresta da lista interna.

        # Remove a aresta das listas de arestas dos nós conectados.
        if aresta_para_deletar in aresta_para_deletar.no_origem.arestas: aresta_para_deletar.no_origem.arestas.remove(aresta_para_deletar)
        if aresta_para_deletar in aresta_para_deletar.no_destino.arestas: aresta_para_deletar.no_destino.arestas.remove(aresta_para_deletar)

        if aresta_oposta:
            aresta_oposta.e_reciproca = False # Desativa a flag de reciprocidade.
            aresta_oposta.atualizar_geometria() # Atualiza a geometria da aresta oposta (agora será reta).

        self.grafoAlterado.emit() # Emite o sinal de que o grafo foi alterado.

    def limpar(self):
        """Limpa todos os nós e arestas da cena e das listas internas."""
        self.cena.clear() # Limpa todos os itens da cena.
        self.nos, self.arestas, self.no_selecionado = {}, [], None # Reinicializa as listas e o nó selecionado.

    def gerar_matriz_adjacencia(self):
        """Gera a matriz de adjacência do grafo atual."""
        rotulos = sorted(self.nos.keys()) # Obtém os rótulos dos nós em ordem alfabética.
        tamanho = len(rotulos)           # Número de nós.
        mapa_indice = {rotulo: i for i, rotulo in enumerate(rotulos)} # Mapeia rótulos para índices.
        mat = [[0] * tamanho for _ in range(tamanho)] # Inicializa a matriz com zeros.

        for aresta in self.arestas:
            # Obtém os índices dos nós de origem e destino da aresta.
            i, j = mapa_indice[aresta.no_origem.rotulo], mapa_indice[aresta.no_destino.rotulo]
            mat[i][j] = aresta.peso # Define o peso na matriz.
            if not self.e_direcionada:
                mat[j][i] = aresta.peso # Se não for direcionado, a matriz é simétrica.
        return rotulos, mat # Retorna os rótulos e a matriz de adjacência.

    def atualizar_da_matriz(self, rotulos, matriz):
        """Atualiza o grafo na visualização com base em uma nova matriz de adjacência."""
        self.limpar() # Limpa o grafo atual.
        n = len(rotulos)
        if n == 0:
            return # Não faz nada se não houver rótulos.

        # Calcula posições para os nós em um círculo.
        centro_x, centro_y, raio = self.width() / 2, self.height() / 2, min(self.width(), self.height()) * 0.35
        for i, rotulo in enumerate(rotulos):
            angulo = 2 * pi * i / n # Calcula o ângulo para posicionar o nó.
            self.adicionar_no(rotulo, centro_x + raio * cos(angulo), centro_y + raio * sin(angulo)) # Adiciona o nó.

        for i in range(n):
            for j in range(n):
                if matriz[i][j] > 0: # Se houver uma conexão (peso > 0).
                    if not self.e_direcionada and j < i:
                        continue # Evita adicionar arestas duplicadas em grafos não direcionados (considera apenas uma direção).
                    self.adicionar_aresta(rotulos[i], rotulos[j], int(matriz[i][j])) # Adiciona a aresta.

    def gerar_nos_aleatorios(self, n_nos):
        """Gera um número especificado de nós aleatoriamente e algumas arestas."""
        self.limpar() # Limpa o grafo existente.
        if n_nos <= 0:
            return

        rotulos = [chr(ord('A') + i) for i in range(n_nos)] # Gera rótulos de 'A' em diante.
        centro_x, centro_y = self.width() / 2, self.height() / 2 # Centro da cena.
        raio = min(centro_x, centro_y) * 0.7 # Raio para distribuir os nós em um círculo.

        for i, rotulo in enumerate(rotulos):
            angulo = 2 * pi * i / n_nos # Calcula o ângulo para posicionar o nó.
            self.adicionar_no(rotulo, centro_x + raio * cos(angulo), centro_y + raio * sin(angulo)) # Adiciona o nó.

        if n_nos <= 1:
            return # Não pode ter arestas se houver 0 ou 1 nó.

        max_arestas = random.randint(n_nos - 1, n_nos * 2) # Número aleatório de arestas a serem geradas.
        chaves_nos = list(self.nos.keys()) # Lista dos rótulos dos nós.
        arestas_existentes, tentativas = set(), 0 # Conjunto para rastrear arestas já adicionadas, e contador de tentativas.

        # Tenta adicionar arestas aleatoriamente até atingir o máximo ou esgotar tentativas.
        while len(self.arestas) < max_arestas and tentativas < max_arestas * 10:
            n1, n2 = random.sample(chaves_nos, 2) # Seleciona dois nós aleatoriamente.
            # Normaliza a tupla da aresta para verificar se já existe (ordem importa para direcionados, não para não direcionados).
            aresta_para_verificar = tuple(sorted((n1, n2))) if not self.e_direcionada else (n1, n2)

            if aresta_para_verificar not in arestas_existentes:
                self.adicionar_aresta(n1, n2, random.randint(1, 100)) # Adiciona a aresta com peso aleatório.
                arestas_existentes.add(aresta_para_verificar) # Adiciona ao conjunto de arestas existentes.
            tentativas += 1

    def mousePressEvent(self, event):
        """Manipula eventos de clique do mouse na cena do grafo."""
        item_clicado = self.itemAt(event.pos()) # Obtém o item da cena no ponto do clique.
        item_no = None
        # Verifica se o item clicado é um nó ou o texto de um nó.
        if isinstance(item_clicado, ItemNo):
            item_no = item_clicado
        elif isinstance(item_clicado, QGraphicsTextItem) and isinstance(item_clicado.parentItem(), ItemNo):
            item_no = item_clicado.parentItem()

        # --- MODO: ADICIONAR NÓS ---
        if self.modo_adicionar_nos:
            if item_clicado is None: # Se não clicou em nenhum item existente.
                # Gera um rótulo sequencial (A, B, C...) para o novo nó.
                rotulo = next((chr(ord('A') + i) for i in range(26) if chr(ord('A') + i) not in self.nos), None)
                if rotulo:
                    # Adiciona o nó na posição clicada na cena.
                    self.adicionar_no(rotulo, self.mapToScene(event.pos()).x(), self.mapToScene(event.pos()).y())
                    self.grafoAlterado.emit() # Emite sinal de alteração.
            return # Retorna para não processar outros modos.

        # --- MODO: DELETAR ITENS ---
        if self.modo_deletar:
            if isinstance(item_clicado, ItemAresta):
                self.deletar_aresta(item_clicado) # Deleta a aresta clicada.
            elif item_no:
                self.deletar_no(item_no) # Deleta o nó clicado.
            elif isinstance(item_clicado, QGraphicsTextItem):
                # Se clicou no texto de uma aresta, encontra a aresta e a deleta.
                texto_aresta = next((e for e in self.arestas if e.item_texto_aresta == item_clicado), None)
                if texto_aresta: self.deletar_aresta(texto_aresta)
            return # Retorna para não processar outros modos.

        # --- MODO: EDITAR RÓTULO DO NÓ ---
        if self.modo_editar_nos:
            if item_no:
                self.editar_rotulo_no(item_no) # Abre diálogo para editar o rótulo do nó.
            return # Retorna para não processar outros modos.

        # --- MODO: EDITAR PESO DA ARESTA ---
        if self.modo_editar_pesos:
            aresta_para_editar = None
            if isinstance(item_clicado, ItemAresta):
                aresta_para_editar = item_clicado
            elif isinstance(item_clicado, QGraphicsTextItem):
                # Se clicou no texto de uma aresta, encontra a aresta.
                texto_aresta = next((e for e in self.arestas if e.item_texto_aresta == item_clicado), None)
                if texto_aresta: aresta_para_editar = texto_aresta
            if aresta_para_editar:
                self.editar_peso_aresta(aresta_para_editar) # Abre diálogo para editar o peso da aresta.
                return # Retorna para não processar outros modos.

        # --- LÓGICA DE SELEÇÃO E CRIAÇÃO DE ARESTAS (MODO PADRÃO) ---
        if item_no: # Se um nó foi clicado.
            if self.no_selecionado: # Se já havia um nó selecionado.
                if self.no_selecionado != item_no: # Se clicou em um nó diferente do já selecionado.
                    # Abre um diálogo para perguntar o peso da nova aresta.
                    peso, ok = QInputDialog.getInt(self, "Peso da Aresta", "Digite o peso:", 1, 1, 999)
                    if ok: self.adicionar_aresta(self.no_selecionado.rotulo, item_no.rotulo, peso) # Adiciona a aresta.
                    self.no_selecionado.definir_selecionado(False) # Desseleciona o nó anterior.
                    self.no_selecionado = None # Limpa a seleção.
                else: # Se clicou no mesmo nó que já estava selecionado.
                    self.no_selecionado.definir_selecionado(False) # Desseleciona o nó.
                    self.no_selecionado = None # Limpa a seleção.
                return # Retorna após processar a seleção/criação de aresta.
            else: # Se nenhum nó estava selecionado.
                self.no_selecionado = item_no # Seleciona o nó clicado.
                self.no_selecionado.definir_selecionado(True) # Ativa o estado de selecionado (e sombra).
        elif self.no_selecionado: # Se clicou em um espaço vazio, mas havia um nó selecionado.
            self.no_selecionado.definir_selecionado(False) # Desseleciona o nó.
            self.no_selecionado = None # Limpa a seleção.
        super().mousePressEvent(event) # Chama o manipulador de eventos da classe base.

    def editar_rotulo_no(self, item_no):
        """Permite ao usuário editar o rótulo de um nó."""
        rotulo_atual = item_no.rotulo
        novo_rotulo, ok = QInputDialog.getText(self, "Alterar Rótulo do Nó", "Novo rótulo:", text=rotulo_atual)
        if ok and novo_rotulo and novo_rotulo != rotulo_atual:
            if novo_rotulo in self.nos: # Verifica se o novo rótulo já está em uso.
                QMessageBox.warning(self, "Rótulo Inválido", f"O rótulo '{novo_rotulo}' já está em uso.")
                return
            self.nos[novo_rotulo] = self.nos.pop(rotulo_atual) # Atualiza o dicionário de nós com o novo rótulo.
            item_no.definir_rotulo(novo_rotulo) # Define o novo rótulo no objeto ItemNo.
            self.grafoAlterado.emit() # Emite sinal de alteração.

    def editar_peso_aresta(self, aresta):
        """Permite ao usuário editar o peso de uma aresta."""
        novo_peso, ok = QInputDialog.getInt(self, "Alterar Peso", "Novo peso:", aresta.peso, 1, 999)
        if ok and novo_peso != aresta.peso: # Se o usuário inseriu um novo peso válido.
            aresta.definir_peso(novo_peso) # Define o novo peso na aresta.
            self.grafoAlterado.emit() # Emite sinal de alteração.

    def deletar_no(self, no_para_deletar):
        """Deleta um nó e todas as arestas conectadas a ele."""
        if no_para_deletar.rotulo not in self.nos: # Verifica se o nó existe.
            return
        arestas_para_remover = list(no_para_deletar.arestas) # Cria uma cópia da lista de arestas para evitar problemas durante a iteração.
        for aresta in arestas_para_remover:
            self.deletar_aresta(aresta) # Deleta cada aresta conectada.
        del self.nos[no_para_deletar.rotulo] # Remove o nó do dicionário.
        if no_para_deletar.scene():
            self.cena.removeItem(no_para_deletar) # Remove o nó da cena.
        self.grafoAlterado.emit() # Emite sinal de alteração.

# =================================================================================
#  FUNÇÕES DE MANIPULAÇÃO E CÁLCULO DE GRAFO (NETWORKX)
# =================================================================================

def construir_grafo_nx_da_matriz(rotulos, matriz, e_direcionado=False):
    """Constrói um objeto NetworkX Graph ou DiGraph a partir de rótulos e uma matriz de adjacência."""
    # Cria um grafo direcionado (DiGraph) ou não direcionado (Graph) com base na flag 'e_direcionado'.
    G = nx.DiGraph() if e_direcionado else nx.Graph()
    G.add_nodes_from(rotulos) # Adiciona todos os nós ao grafo.
    for i in range(len(rotulos)):
        for j in range(len(rotulos)):
            if matriz[i][j] > 0: # Se houver um peso positivo na matriz.
                # Adiciona uma aresta entre os nós correspondentes, com o peso especificado.
                G.add_edge(rotulos[i], rotulos[j], weight=matriz[i][j])
    return G

def obter_todas_rotas(G, origem, destino, max_nos=None):
    """Obtém todas as rotas simples entre uma origem e um destino em um grafo NetworkX."""
    # Utiliza a função all_simple_paths do NetworkX para encontrar todas as rotas simples.
    # 'cutoff' limita o comprimento máximo do caminho (número de nós).
    return list(nx.all_simple_paths(G, source=origem, target=destino, cutoff=max_nos))

def obter_caminho_mais_curto(G, origem, destino):
    """Obtém o caminho mais curto (menor custo) entre uma origem e um destino usando o algoritmo de Dijkstra."""
    try:
        # Usa dijkstra_path do NetworkX, que encontra o caminho de menor custo em grafos ponderados.
        return nx.dijkstra_path(G, origem, destino, weight='weight')
    except nx.NetworkXNoPath:
        return None # Retorna None se não houver caminho.

def obter_caminho_mais_longo_seguro(G, origem, destino, todas_rotas):
    """Obtém o caminho mais longo (maior custo) entre uma origem e um destino a partir de uma lista de todas as rotas."""
    if not todas_rotas:
        return None # Retorna None se não houver rotas.
    # Encontra o caminho com o maior 'weight' (custo total) entre todas as rotas fornecidas.
    return max(todas_rotas, key=lambda caminho: nx.path_weight(G, caminho, weight='weight'))

def calcular_e_formatar_rotas(visualizador_grafo: 'VisualizadorGrafo', origem: str, destino: str) -> str:
    """
    Calcula e formata as informações de rotas (melhor, pior, outras) entre dois nós
    em um grafo visualizador e retorna uma string formatada.
    """
    # Verifica se os nós de origem e destino existem no grafo visualizador.
    if not (origem in visualizador_grafo.nos and destino in visualizador_grafo.nos):
        return "Nó de origem ou destino não encontrado no grafo."

    # Gera a matriz de adjacência do grafo atual na visualização.
    rotulos, matriz = visualizador_grafo.gerar_matriz_adjacencia()
    # Constrói um grafo NetworkX a partir da matriz de adjacência.
    G = construir_grafo_nx_da_matriz(rotulos, matriz, visualizador_grafo.e_direcionada)

    try:
        # Obtém todas as rotas simples entre a origem e o destino.
        todas_rotas = obter_todas_rotas(G, origem, destino)
        if not todas_rotas:
            return f"Nenhuma rota encontrada entre {origem} e {destino}."

        # Calcula o custo total para cada rota.
        rotas_com_custo = [{'caminho': caminho, 'custo': nx.path_weight(G, caminho, weight='weight')} for caminho in todas_rotas]
        rotas_com_custo.sort(key=lambda x: x['custo']) # Ordena as rotas pelo custo (do menor para o maior).

        # Constrói a string de resultado formatada.
        string_resultado = f"Análise de Rota de {origem} para {destino}\n" + "=" * 40 + "\n\n"

        # Adiciona a melhor rota (menor custo).
        melhor_rota = rotas_com_custo[0]
        string_resultado += f"🏆 Melhor Rota (Custo Mínimo):\n   - Caminho: {' → '.join(melhor_rota['caminho'])}\n   - Custo Total: {melhor_rota['custo']}\n\n"

        # Se houver mais de uma rota, adiciona a pior rota (maior custo).
        if len(rotas_com_custo) > 1:
            pior_rota = rotas_com_custo[-1]
            string_resultado += f"🚧 Pior Rota (Custo Máximo):\n   - Caminho: {' → '.join(pior_rota['caminho'])}\n   - Custo Total: {pior_rota['custo']}\n\n"

        # Se houver mais de duas rotas, lista as outras rotas possíveis.
        if len(rotas_com_custo) > 2:
            string_resultado += "🗺️ Outras Rotas Possíveis:\n"
            for i, info_rota in enumerate(rotas_com_custo[1:-1]): # Exclui a melhor e a pior.
                string_resultado += f" {i + 1}. Caminho: {' → '.join(info_rota['caminho'])}\n     Custo: {info_rota['custo']}\n"

        return string_resultado.strip() # Retorna a string formatada, removendo espaços em branco extras.

    except nx.NetworkXNoPath:
        return f"Nenhuma rota encontrada entre {origem} e {destino}." # Mensagem se não houver caminho.
    except nx.NodeNotFound:
        return "Nó de origem ou destino não encontrado no grafo." # Mensagem se o nó não for encontrado.
    except Exception as e:
        return f"Ocorreu um erro inesperado: {e}" # Mensagem para outros erros inesperados.