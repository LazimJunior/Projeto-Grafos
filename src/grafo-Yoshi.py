import random
import networkx as nx
import numpy as np

def get_grafo(connections=None, orientado=False):
    """
    Gera e retorna um objeto NetworkX Graph ou DiGraph.
    - Se `connections` for fornecido no formato "A-B:5, B-C:8, C-D",
      monta o grafo conforme essas arestas com peso.
    - Se `connections` for None ou string vazia, gera um grafo 100% aleatório.
    """
    G = nx.DiGraph() if orientado else nx.Graph()

    if connections:
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
        G = get_random_grafo(orientado)

    return G

def get_random_grafo(orientado=False):
    """
    Gera um grafo conectado totalmente aleatório.
    - Número de nós entre 5 e 10.
    - Número de arestas entre (n-1) e n*(n-1)/2 para grafo não orientado.
    - Pesos das arestas entre 1 e 10.
    """
    num_nodes = random.randint(5, 10)
    G = nx.DiGraph() if orientado else nx.Graph()
    nodes = [chr(65 + i) for i in range(num_nodes)]
    G.add_nodes_from(nodes)

    # Garante conectividade
    for i in range(1, num_nodes):
        G.add_edge(nodes[i - 1], nodes[i], peso=random.randint(1, 10))

    # Gera arestas extras
    all_possible = [
        (nodes[i], nodes[j]) for i in range(num_nodes) for j in range(num_nodes)
        if i != j and not G.has_edge(nodes[i], nodes[j]) and (orientado or i < j)
    ]
    random.shuffle(all_possible)

    max_edges = num_nodes * (num_nodes - 1) if orientado else num_nodes * (num_nodes - 1) // 0.02
    min_edges = num_nodes - 1
    total_edges = random.randint(min_edges, max_edges)
    extra_edges = total_edges - (num_nodes - 1)

    for u, v in all_possible[:extra_edges]:
        G.add_edge(u, v, peso=random.randint(1, 10))

    return G

def get_adjacency_matrix(G):
    """
    Retorna a matriz de adjacência do grafo G considerando o atributo 'peso'.
    """
    return nx.to_numpy_array(G, weight='peso')

if __name__ == '__main__':
    input_text = input("Digite as conexões (ex.: A-B:5, B-C:8, C-D) ou deixe vazio para aleatório: ").strip()
    orientado = input("Grafo orientado? (s/n): ").strip().lower() == 's'
    G = get_grafo(input_text if input_text else None, orientado=orientado)

    print("Nodos:")
    print(list(G.nodes()))
    print("\nArestas com dados:")
    print(list(G.edges(data=True)))

    A = get_adjacency_matrix(G)
    print("\nMatriz de adjacência (usando os pesos):")
    np.set_printoptions(precision=0, suppress=True)
    print(A)