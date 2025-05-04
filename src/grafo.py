import random
import networkx as nx
import numpy as np

def get_grafo(connections=None):
    """
    Gera e retorna um objeto NetworkX Graph.
    - Se `connections` for fornecido no formato "A-B:5, B-C:8, C-D",
      monta o grafo conforme essas arestas com peso.
    - Se `connections` for None ou string vazia, gera um grafo 100% aleatório.
    """
    if connections:
        G = nx.Graph()
        tokens = [token.strip() for token in connections.split(',') if token.strip()]
        for token in tokens:
            if ':' in token:
                conn_part, weight_str = token.split(':', 1)
                try:
                    weight = int(weight_str.strip())
                except ValueError:
                    weight = random.randint(1, 10)
            else:
                conn_part = token
                weight = random.randint(1, 10)

            nodes = [n.strip() for n in conn_part.split('-') if n.strip()]
            for i in range(len(nodes) - 1):
                G.add_edge(nodes[i], nodes[i + 1], peso=weight)
    else:
        # Grafo totalmente aleatório
        G = get_random_grafo()

    return G

def get_random_grafo():
    """
    Gera um grafo conectado totalmente aleatório.
    - Número de nós escolhido aleatoriamente entre 5 e 15.
    - Número de arestas aleatório entre (n-1) e n*(n-1)/2.
    - Pesos das arestas aleatórios entre 1 e 10.
    """
    # Escolhe aleatoriamente quantos nós
    num_nodes = random.randint(5, 10)
    # Máximo possível de arestas em grafo simples
    max_edges = num_nodes * (num_nodes - 1) // 2
    # Garante pelo menos (num_nodes - 1) para manter conectividade
    num_edges = random.randint(num_nodes - 1, max_edges)

    G = nx.Graph()
    # Rótulos A, B, C, ...
    nodes = [chr(65 + i) for i in range(num_nodes)]
    G.add_nodes_from(nodes)

    # Conecta sequencialmente para garantir conectividade
    for i in range(1, num_nodes):
        G.add_edge(nodes[i-1], nodes[i], peso=random.randint(1, 10))

    # Lista de possíveis arestas ainda não usadas
    possible = [
        (nodes[i], nodes[j])
        for i in range(num_nodes)
        for j in range(i+1, num_nodes)
        if not G.has_edge(nodes[i], nodes[j])
    ]
    random.shuffle(possible)

    extra = num_edges - (num_nodes - 1)
    for u, v in possible[:extra]:
        G.add_edge(u, v, peso=random.randint(1, 10))

    return G

def get_adjacency_matrix(G):
    """
    Retorna a matriz de adjacência do grafo G considerando o atributo 'peso'.
    A posição (i, j) será zero se não houver aresta entre os nós i e j.
    """
    return nx.to_numpy_array(G, weight='peso')

if __name__ == '__main__':
    # Teste das funções
    input_text = input("Digite as conexões (ex.: A-B:5, B-C:8, C-D) ou deixe vazio para aleatório: ").strip()
    G = get_grafo(input_text if input_text != '' else None)

    print("Nodos:")
    print(list(G.nodes()))
    print("\nArestas com dados:")
    print(list(G.edges(data=True)))

    A = get_adjacency_matrix(G)
    print("\nMatriz de adjacência (usando os pesos):")
    np.set_printoptions(precision=0, suppress=True)
    print(A.astype(int))

    # Teste do grafo aleatório com número específico de nós e arestas
    print("\nTeste do grafo aleatório:")
    G_random = get_random_grafo(5, 7)
    print("Nodos:", list(G_random.nodes()))
    print("Arestas:", list(G_random.edges(data=True)))
    print("Matriz de adjacência:")
    print(nx.to_numpy_array(G_random, weight='peso').astype(int))

    # Plot para visualização (opcional)
    pos = nx.spring_layout(G)
    plt.figure(figsize=(6, 6))
    nx.draw_networkx(G, pos=pos, with_labels=True, node_color="#7FB3D5", edge_color="#4A4A4A")
    plt.show()