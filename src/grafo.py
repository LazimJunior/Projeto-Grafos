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
        super().__init__(-raio, -raio, 2 * raio, 2 * raio)
        self.arestas = []
        self.raio = raio
        # Flags que permitem que o item seja móvel e selecionável
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable)
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges)

        self.pincel_normal = QBrush(QColor("#5E81AC"))
        self.pincel_selecionado = QBrush(QColor("#88C0D0"))
        self.setBrush(self.pincel_normal)
        self.setPen(QPen(QColor("#88C0D0"), 2))

        self.sombra = QGraphicsDropShadowEffect()
        self.sombra.setBlurRadius(15)
        self.sombra.setColor(QColor("#88C0D0"))
        self.sombra.setOffset(QPointF(0, 0))

        self.setGraphicsEffect(self.sombra)
        self.sombra.setEnabled(False)
        self.item_texto = QGraphicsTextItem(rotulo, self)
        font = QFont("Segoe UI", 11, QFont.Bold)
        self.item_texto.setFont(font)
        self.item_texto.setDefaultTextColor(QColor("#ECEFF4"))
        self.setPos(x, y)
        self.rotulo = rotulo
        self.definir_rotulo(rotulo)

    def adicionar_aresta(self, aresta):
        if aresta not in self.arestas:
            self.arestas.append(aresta)

    def definir_rotulo(self, novo_rotulo):
        """Atualiza o rótulo do nó e centraliza o texto."""
        self.rotulo = novo_rotulo
        self.item_texto.setPlainText(novo_rotulo)
        self.item_texto.setPos(-self.item_texto.boundingRect().width() / 2, -self.item_texto.boundingRect().height() / 2)

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.ItemPositionHasChanged:
            for aresta in self.arestas:
                aresta.atualizar_geometria()
        return super().itemChange(change, value)

    def definir_selecionado(self, esta_selecionado):
        self.sombra.setEnabled(esta_selecionado)
        self.setBrush(self.pincel_selecionado if esta_selecionado else self.pincel_normal)

class ItemAresta(QGraphicsLineItem):
    """Representa uma aresta, com lógica para desenhar linhas retas ou curvas."""

    def __init__(self, no_origem: ItemNo, no_destino: ItemNo, peso: int = 1, e_direcionada=False):
        super().__init__()
        self.no_origem = no_origem
        self.no_destino = no_destino
        self.peso = peso
        self.e_direcionada = e_direcionada
        self.tamanho_seta = 12
        self.e_reciproca = False

        self._caminho = QPainterPath()
        self.setZValue(-1)
        self.caneta_linha = QPen(QColor("#4C566A"), 2.5)
        self.setPen(self.caneta_linha)

        self.item_texto_aresta = QGraphicsTextItem(str(self.peso))
        font = QFont("Segoe UI", 10)
        self.item_texto_aresta.setFont(font)
        self.item_texto_aresta.setDefaultTextColor(QColor("#D8DEE9"))

        self.no_origem.adicionar_aresta(self)
        self.no_destino.adicionar_aresta(self)
        self.atualizar_geometria()

    def adicionar_texto_a_cena(self, cena):
        cena.addItem(self.item_texto_aresta)

    def definir_peso(self, peso):
        self.peso = peso
        self.item_texto_aresta.setPlainText(str(self.peso))

    def boundingRect(self):
        return self._caminho.boundingRect().adjusted(-20, -20, 20, 20)

    def shape(self):
        return self._caminho

    def atualizar_geometria(self):
        self.prepareGeometryChange()
        p1 = self.no_origem.pos()
        p2 = self.no_destino.pos()

        angulo_linha_rad = atan2(p2.y() - p1.y(), p2.x() - p1.x())
        dx_origem = cos(angulo_linha_rad) * self.no_origem.raio
        dy_origem = sin(angulo_linha_rad) * self.no_origem.raio
        ponto_inicial = p1 + QPointF(dx_origem, dy_origem)

        dx_destino = cos(angulo_linha_rad) * self.no_destino.raio
        dy_destino = sin(angulo_linha_rad) * self.no_destino.raio
        ponto_final = p2 - QPointF(dx_destino, dy_destino)

        self._caminho = QPainterPath(ponto_inicial)

        if self.e_reciproca:
            dx, dy = p2.x() - p1.x(), p2.y() - p1.y()
            ponto_meio = (ponto_inicial + ponto_final) / 2
            perp_dx, perp_dy = -dy, dx
            norm = sqrt(perp_dx ** 2 + perp_dy ** 2)
            perp_dx, perp_dy = (perp_dx / norm, perp_dy / norm) if norm > 0 else (0, 0)

            distancia_deslocamento = 30
            if self.no_origem.rotulo > self.no_destino.rotulo:
                distancia_deslocamento *= -1

            ponto_controle = ponto_meio + QPointF(perp_dx * distancia_deslocamento, perp_dy * distancia_deslocamento)
            self._caminho.quadTo(ponto_controle, ponto_final)
        else:
            self._caminho.lineTo(ponto_final)

        posicao_texto = self._caminho.pointAtPercent(0.5)
        self.item_texto_aresta.setPos(posicao_texto)
        self.update()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.caneta_linha)
        painter.drawPath(self._caminho)

        if self.e_direcionada:
            painter.setBrush(QBrush(QColor("#88C0D0")))
            angulo_no_fim = self._caminho.angleAtPercent(1)
            self.desenhar_seta(painter, self._caminho.pointAtPercent(1), angulo_no_fim)

    def desenhar_seta(self, painter, ponto, angulo_graus):
        s = self.tamanho_seta
        cabeca_seta = QPolygonF([
            QPointF(0, 0),
            QPointF(-s, -s / 2.5),
            QPointF(-s, s / 2.5)
        ])

        transformar = QTransform()
        transformar.translate(ponto.x(), ponto.y())
        transformar.rotate(-angulo_graus)
        painter.drawPolygon(transformar.map(cabeca_seta))

class VisualizadorGrafo(QGraphicsView):
    grafoAlterado = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing)
        self.cena = QGraphicsScene()
        self.setScene(self.cena)
        self.nos, self.arestas = {}, []
        self.e_direcionada = False
        self.setBackgroundBrush(QBrush(QColor("#262b33")))
        self.no_selecionado = None
        self.modo_adicionar_nos = False
        self.modo_editar_nos = False
        self.modo_editar_pesos = False
        self.modo_deletar = False

    def definir_tipo_grafo(self, e_direcionada: bool):
        self.e_direcionada = e_direcionada

    def definir_modo_adicionar_nos(self, ativado: bool):
        self.modo_adicionar_nos = ativado
        self.setCursor(Qt.PointingHandCursor if ativado else Qt.ArrowCursor)

    def definir_modo_editar_nos(self, ativado: bool):
        self.modo_editar_nos = ativado
        self.setCursor(Qt.IBeamCursor if ativado else Qt.ArrowCursor)

    def definir_modo_editar_pesos(self, ativado: bool):
        self.modo_editar_pesos = ativado
        self.setCursor(Qt.IBeamCursor if ativado else Qt.ArrowCursor)

    def definir_modo_deletar(self, ativado: bool):
        self.modo_deletar = ativado
        self.setCursor(Qt.CrossCursor if ativado else Qt.ArrowCursor)

    def adicionar_no(self, rotulo, x, y):
        if rotulo in self.nos: return
        no = ItemNo(rotulo, x, y)
        self.nos[rotulo] = no
        self.cena.addItem(no)

    def adicionar_aresta(self, rotulo1, rotulo2, peso):
        no1, no2 = self.nos.get(rotulo1), self.nos.get(rotulo2)
        if not (no1 and no2) or any(e.no_origem == no1 and e.no_destino == no2 for e in self.arestas):
            return
        nova_aresta = ItemAresta(no1, no2, peso, self.e_direcionada)
        if self.e_direcionada:
            aresta_oposta = next((e for e in self.arestas if e.no_origem == no2 and e.no_destino == no1), None)
            if aresta_oposta:
                nova_aresta.e_reciproca = True
        self.arestas.append(nova_aresta)
        self.cena.addItem(nova_aresta)
        nova_aresta.adicionar_texto_a_cena(self.cena)
        nova_aresta.atualizar_geometria()
        self.grafoAlterado.emit()

    def deletar_aresta(self, aresta_para_deletar):
        if aresta_para_deletar not in self.arestas: return
        aresta_oposta = next((e for e in self.arestas if
                              e.no_origem == aresta_para_deletar.no_destino and e.no_destino == aresta_para_deletar.no_origem),
                             None)
        if aresta_para_deletar.scene():
            self.cena.removeItem(aresta_para_deletar.item_texto_aresta)
            self.cena.removeItem(aresta_para_deletar)
        self.arestas.remove(aresta_para_deletar)
        if aresta_para_deletar in aresta_para_deletar.no_origem.arestas: aresta_para_deletar.no_origem.arestas.remove(aresta_para_deletar)
        if aresta_para_deletar in aresta_para_deletar.no_destino.arestas: aresta_para_deletar.no_destino.arestas.remove(aresta_para_deletar)
        if aresta_oposta:
            aresta_oposta.e_reciproca = False
            aresta_oposta.atualizar_geometria()
        self.grafoAlterado.emit()

    def limpar(self):
        self.cena.clear()
        self.nos, self.arestas, self.no_selecionado = {}, [], None

    def gerar_matriz_adjacencia(self):
        rotulos = sorted(self.nos.keys())
        tamanho = len(rotulos)
        mapa_indice = {rotulo: i for i, rotulo in enumerate(rotulos)}
        mat = [[0] * tamanho for _ in range(tamanho)]
        for aresta in self.arestas:
            i, j = mapa_indice[aresta.no_origem.rotulo], mapa_indice[aresta.no_destino.rotulo]
            mat[i][j] = aresta.peso
            if not self.e_direcionada:
                mat[j][i] = aresta.peso
        return rotulos, mat

    def atualizar_da_matriz(self, rotulos, matriz):
        self.limpar()
        n = len(rotulos)
        if n == 0: return
        centro_x, centro_y, raio = self.width() / 2, self.height() / 2, min(self.width(), self.height()) * 0.35
        for i, rotulo in enumerate(rotulos):
            angulo = 2 * pi * i / n
            self.adicionar_no(rotulo, centro_x + raio * cos(angulo), centro_y + raio * sin(angulo))
        for i in range(n):
            for j in range(n):
                if matriz[i][j] > 0:
                    if not self.e_direcionada and j < i: continue
                    self.adicionar_aresta(rotulos[i], rotulos[j], int(matriz[i][j]))

    def gerar_nos_aleatorios(self, n_nos):
        self.limpar()
        if n_nos <= 0: return
        rotulos = [chr(ord('A') + i) for i in range(n_nos)]
        centro_x, centro_y = self.width() / 2, self.height() / 2
        raio = min(centro_x, centro_y) * 0.7
        for i, rotulo in enumerate(rotulos):
            angulo = 2 * pi * i / n_nos
            self.adicionar_no(rotulo, centro_x + raio * cos(angulo), centro_y + raio * sin(angulo))
        if n_nos <= 1: return
        max_arestas = random.randint(n_nos - 1, n_nos * 2)
        chaves_nos = list(self.nos.keys())
        arestas_existentes, tentativas = set(), 0
        while len(self.arestas) < max_arestas and tentativas < max_arestas * 10:
            n1, n2 = random.sample(chaves_nos, 2)
            aresta_para_verificar = tuple(sorted((n1, n2))) if not self.e_direcionada else (n1, n2)
            if aresta_para_verificar not in arestas_existentes:
                self.adicionar_aresta(n1, n2, random.randint(1, 100))
                arestas_existentes.add(aresta_para_verificar)
            tentativas += 1

    def mousePressEvent(self, event):
        item_clicado = self.itemAt(event.pos())
        item_no = None
        if isinstance(item_clicado, ItemNo):
            item_no = item_clicado
        elif isinstance(item_clicado, QGraphicsTextItem) and isinstance(item_clicado.parentItem(), ItemNo):
            item_no = item_clicado.parentItem()

        # --- MODO: ADICIONAR NÓS ---
        if self.modo_adicionar_nos:
            if item_clicado is None:
                rotulo = next((chr(ord('A') + i) for i in range(26) if chr(ord('A') + i) not in self.nos), None)
                if rotulo:
                    self.adicionar_no(rotulo, self.mapToScene(event.pos()).x(), self.mapToScene(event.pos()).y())
                    self.grafoAlterado.emit()
            return

        # --- MODO: DELETAR ITENS ---
        if self.modo_deletar:
            if isinstance(item_clicado, ItemAresta):
                self.deletar_aresta(item_clicado)
            elif item_no:
                self.deletar_no(item_no)
            elif isinstance(item_clicado, QGraphicsTextItem):
                texto_aresta = next((e for e in self.arestas if e.item_texto_aresta == item_clicado), None)
                if texto_aresta: self.deletar_aresta(texto_aresta)
            return

        # --- MODO: EDITAR RÓTULO DO NÓ ---
        if self.modo_editar_nos:
            if item_no:
                self.editar_rotulo_no(item_no)
            return

        # --- MODO: EDITAR PESO DA ARESTA ---
        if self.modo_editar_pesos:
            aresta_para_editar = None
            if isinstance(item_clicado, ItemAresta):
                aresta_para_editar = item_clicado
            elif isinstance(item_clicado, QGraphicsTextItem):
                texto_aresta = next((e for e in self.arestas if e.item_texto_aresta == item_clicado), None)
                if texto_aresta: aresta_para_editar = texto_aresta
            if aresta_para_editar:
                self.editar_peso_aresta(aresta_para_editar)
                return

        # --- LÓGICA DE SELEÇÃO E CRIAÇÃO DE ARESTAS (MODO PADRÃO) ---
        if item_no:
            if self.no_selecionado:
                if self.no_selecionado != item_no:
                    peso, ok = QInputDialog.getInt(self, "Peso da Aresta", "Digite o peso:", 1, 1, 999)
                    if ok: self.adicionar_aresta(self.no_selecionado.rotulo, item_no.rotulo, peso)
                    self.no_selecionado.definir_selecionado(False)
                    self.no_selecionado = None
                else:
                    self.no_selecionado.definir_selecionado(False)
                    self.no_selecionado = None
                return
            else:
                self.no_selecionado = item_no
                self.no_selecionado.definir_selecionado(True)
        elif self.no_selecionado:
            self.no_selecionado.definir_selecionado(False)
            self.no_selecionado = None
        super().mousePressEvent(event)

    def editar_rotulo_no(self, item_no):
        rotulo_atual = item_no.rotulo
        novo_rotulo, ok = QInputDialog.getText(self, "Alterar Rótulo do Nó", "Novo rótulo:", text=rotulo_atual)
        if ok and novo_rotulo and novo_rotulo != rotulo_atual:
            if novo_rotulo in self.nos:
                QMessageBox.warning(self, "Rótulo Inválido", f"O rótulo '{novo_rotulo}' já está em uso.")
                return
            self.nos[novo_rotulo] = self.nos.pop(rotulo_atual)
            item_no.definir_rotulo(novo_rotulo)
            self.grafoAlterado.emit()

    def editar_peso_aresta(self, aresta):
        novo_peso, ok = QInputDialog.getInt(self, "Alterar Peso", "Novo peso:", aresta.peso, 1, 999)
        if ok and novo_peso != aresta.peso:
            aresta.definir_peso(novo_peso)
            self.grafoAlterado.emit()

    def deletar_no(self, no_para_deletar):
        if no_para_deletar.rotulo not in self.nos: return
        arestas_para_remover = list(no_para_deletar.arestas)
        for aresta in arestas_para_remover:
            self.deletar_aresta(aresta)
        del self.nos[no_para_deletar.rotulo]
        if no_para_deletar.scene():
            self.cena.removeItem(no_para_deletar)
        self.grafoAlterado.emit()

# =================================================================================
#  FUNÇÕES DE MANIPULAÇÃO E CÁLCULO DE GRAFO (NETWORKX)
# =================================================================================

def construir_grafo_nx_da_matriz(rotulos, matriz, e_direcionado=False):
    G = nx.DiGraph() if e_direcionado else nx.Graph()
    G.add_nodes_from(rotulos)
    for i in range(len(rotulos)):
        for j in range(len(rotulos)):
            if matriz[i][j] > 0:
                G.add_edge(rotulos[i], rotulos[j], weight=matriz[i][j])
    return G

def obter_todas_rotas(G, origem, destino, max_nos=None):
    return list(nx.all_simple_paths(G, source=origem, target=destino, cutoff=max_nos))

def obter_caminho_mais_curto(G, origem, destino):
    try:
        return nx.dijkstra_path(G, origem, destino, weight='weight')
    except nx.NetworkXNoPath:
        return None

def obter_caminho_mais_longo_seguro(G, origem, destino, todas_rotas):
    if not todas_rotas:
        return None
    return max(todas_rotas, key=lambda caminho: nx.path_weight(G, caminho, weight='weight'))

def calcular_e_formatar_rotas(visualizador_grafo: 'VisualizadorGrafo', origem: str, destino: str) -> str:
    if not (origem in visualizador_grafo.nos and destino in visualizador_grafo.nos):
        return "Nó de origem ou destino não encontrado no grafo."
    rotulos, matriz = visualizador_grafo.gerar_matriz_adjacencia()
    G = construir_grafo_nx_da_matriz(rotulos, matriz, visualizador_grafo.e_direcionada)
    try:
        todas_rotas = obter_todas_rotas(G, origem, destino)
        if not todas_rotas:
            return f"Nenhuma rota encontrada entre {origem} e {destino}."
        rotas_com_custo = [{'caminho': caminho, 'custo': nx.path_weight(G, caminho, weight='weight')} for caminho in todas_rotas]
        rotas_com_custo.sort(key=lambda x: x['custo'])
        string_resultado = f"Análise de Rota de {origem} para {destino}\n" + "=" * 40 + "\n\n"
        melhor_rota = rotas_com_custo[0]
        string_resultado += f"🏆 Melhor Rota (Custo Mínimo):\n   - Caminho: {' → '.join(melhor_rota['caminho'])}\n   - Custo Total: {melhor_rota['custo']}\n\n"
        if len(rotas_com_custo) > 1:
            pior_rota = rotas_com_custo[-1]
            string_resultado += f"🚧 Pior Rota (Custo Máximo):\n   - Caminho: {' → '.join(pior_rota['caminho'])}\n   - Custo Total: {pior_rota['custo']}\n\n"
        if len(rotas_com_custo) > 2:
            string_resultado += "🗺️ Outras Rotas Possíveis:\n"
            for i, info_rota in enumerate(rotas_com_custo[1:-1]):
                string_resultado += f" {i + 1}. Caminho: {' → '.join(info_rota['caminho'])}\n     Custo: {info_rota['custo']}\n"
        return string_resultado.strip()
    except nx.NetworkXNoPath:
        return f"Nenhuma rota encontrada entre {origem} e {destino}."
    except nx.NodeNotFound:
        return "Nó de origem ou destino não encontrado no grafo."
    except Exception as e:
        return f"Ocorreu um erro inesperado: {e}"