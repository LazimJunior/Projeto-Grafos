import sys
from PyQt5.QtWidgets import QApplication
from janela_principal import JanelaPrincipal # Importa a classe JanelaPrincipal do módulo janela_principal.

if __name__ == '__main__':
    app = QApplication(sys.argv) # Cria uma instância da aplicação PyQt.
    janela = JanelaPrincipal() # Cria uma instância da JanelaPrincipal (nossa janela principal da interface).
    janela.show() # Exibe a janela principal.
    sys.exit(app.exec_()) # Inicia o loop de eventos da aplicação PyQt e garante uma saída limpa quando a janela é fechada.