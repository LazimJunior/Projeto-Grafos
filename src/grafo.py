import random
import networkx as nx 
import matplotlib.pyplot as plt 

#Criando Grafo vazio 
grafo = nx.Graph() 

#Adicionando vertices
grafo.add_node('vertice_1') 
grafo.add_node('vertice_2') 
grafo.add_node('vertice_3') 
grafo.add_node('vertice_4') 
grafo.add_node('vertice_5')

#Adicionando Arestas
grafo.add_edge('vertice_1', 'vertice_2') 
grafo.add_edge('vertice_2', 'vertice_3') 
grafo.add_edge('vertice_3', 'vertice_4') 
grafo.add_edge('vertice_4', 'vertice_5')
grafo.add_edge('vertice_5', 'vertice_1') 
grafo.add_edge('vertice_2', 'vertice_4') 


#Listando Vétices
print(f'Lista de vertices')
print(f'{grafo.nodes()}\n')
print('\n')
input()

#Percorer o conjunto  de vertices 
print(f'\nPercorrendo conjunto de vertices: \n')
for v in grafo.nodes():
    print(v)
print('\n')
input()

#Listando Arestas
print(f'Lista de Arestas')
print(f'{grafo.edges()}\n')
print('\n')
input()

#Percorre as arestas 
print('Percorendo as arestas:')
for a in grafo.edges():
    print(a)
print('\n')
input()

#Lista de Graus
print(f'Lista de Graus')
print(f'{grafo.degree()}\n')
print('\n')
input()

#Grau de um vertice especifico: vertice_2 
print(f'O grau do Vertice_2 é:{grafo.degree()['vertice_2']}\n')
print('\n')
input()

#Grafo com a lista de adjacências
print('Grafo com a lista de adjacências')
print(grafo['vertice_1'])
print(grafo['vertice_2'])
print(grafo['vertice_3'])
print(grafo['vertice_4'])
print(grafo['vertice_5'])
input()

#Obtem a matrizes de adjacencias do grafo
print('Matriz de adjacencia do grafo')
m = nx.adjacency_matrix(grafo)                   # Retorna a matiz esparsa para economizar memoria
print(m.todense())                               # Converte para matriz densa (padrão)  
input()


# Adiciona um campo peso em cada  aresta do grafo 
grafo['vertice_1']['vertice_2']['peso'] = random.randint(1, 10)
grafo['vertice_2']['vertice_3']['peso'] = random.randint(1, 10)
grafo['vertice_3']['vertice_4']['peso'] = random.randint(1, 10)
grafo['vertice_4']['vertice_5']['peso'] = random.randint(1, 10)
grafo['vertice_5']['vertice_1']['peso'] = random.randint(1, 10)
grafo['vertice_2']['vertice_4']['peso'] = random.randint(1, 10)

#Lista cada aresta e seus respectivos pesos
print('Lista cada aresta com os seus pesos')
for edge in grafo.edges():
    u = edge[0]
    v = edge[1]
    print('O peso da aresta', edge, 'vale ' , grafo[u][v]['peso'])
input()
print()

print('Plotando o grafo como imagem')

plt.figure(2)
#Há varios layouts, mas springs é um dos mais bonitos 
nx.draw_networkx(grafo, pos=nx.spring_layout(grafo), with_labels=True)
plt.show()
