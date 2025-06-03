import sys
from PyQt5.QtWidgets import QApplication
from janela_principal import JanelaPrincipal

if __name__ == '__main__':
    app = QApplication(sys.argv)
    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec_())