#Importando biblioteca
import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QToolTip


#Criação da janela com PyQt5
class janela(QMainWindow):
    def __init__(self):
        super().__init__()

        #Configurações da tela colocar antes de ```self.carregar_janela()```             
        self.topo = 100
        self.esquerda = 100
        self.largura = 800
        self.altura = 600
        self.titulo = "Projeto Grafo"
        
        botao_iniciar = QPushButton('Iniciar', self)
        botao_iniciar.move(500, 100)                    #Precisa centralizar o BOTÃO, cansei  .move(x,y) 
        botao_iniciar.resize(150, 50)                   #Tamanho
        botao_iniciar.styleSheet()                      #Customizar
        botao_iniciar.clicked.connect()                 #Adicionar Função quando acionar o botão
        self.carregar_janela()
               

    def carregar_janela(self):
        self.setGeometry(self.esquerda,self.topo,self.largura,self.altura)
        self.setWindowTitle(self.titulo)
        self.show()
        
    def criar_grafo():
        os.system('cls') #Criar função 



aplicacao = QApplication(sys.argv)
j = janela()
sys.exit(aplicacao.exec())


