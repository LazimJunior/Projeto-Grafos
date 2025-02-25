import random
import networkx as nx 
import matplotlib.pyplot as plt 

#Criando Grafo vazio 
grafo = nx.Graph() 

# Adicionar nós com atributos ao grafo(nome e altura)
grafo.add_edges_from([('A', 'B', {"nome": "Lazim", "peso": random.randint(1, 10)}), 
                      ('B', 'C', {"nome": "Breno", "peso": random.randint(1, 10)}),
                      ('C', 'D', {"nome": "William", "peso": random.randint(1, 10)}),
                      ('D', 'E', {"nome": "Cleslley", "peso": random.randint(1, 10)}),
                      ('E', 'A', {"nome": "Lara", "peso": random.randint(1, 10)})
])

#Adicionando Arestas extras 
grafo.add_edges_from([('B', 'D', {"peso": random.randint(1, 10)}) 
])

#Listando Vétices
print('\nListando os vertices:')
print(list(grafo.nodes))

#Listando Arestas
print('\nListando as arestas:')
print(list(grafo.edges))

#Lista de Graus
print('\nListando os graus')
print(list(grafo.degree))

#Grau de um vertice especifico: B 
print(f'\nO grau do B é:{grafo.degree["B"]}')

#Grafo com a lista de adjacências
print('\nGrafo com a lista de adjacências')
for no in grafo.adj:
    print(list(grafo.adj[no]))

#Obtem a matrizes de adjacencias do grafo
print('\nMatriz de adjacencia do grafo')
m = nx.adjacency_matrix(grafo)                   # Retorna a matiz esparsa para economizar memoria
print(m.todense())                               # Converte para matriz densa (padrão)  

#Lista cada aresta e seus respectivos pesos
print('\nLista cada aresta com os seus pesos')
for edge in grafo.edges():
    u = edge[0]
    v = edge[1]
    print('O peso da aresta', edge, 'vale ' , grafo[u][v]["peso"])
input("Precione qualquer tecla, para plotar o grafo.")
print()

print('\nPlotando o grafo como imagem')

plt.figure(2)
#Há varios layouts, mas springs é um dos mais bonitos 
nx.draw_networkx(grafo, pos=nx.spring_layout(grafo), with_labels=True)
plt.show()