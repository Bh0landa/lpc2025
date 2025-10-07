import random

FRASE_ALVO = "METHINKS IT IS LIKE A WEASEL"
TAMANHO_POPULACAO = 100
TAXA_MUTACAO = 0.05
CARACTERES = "ABCDEFGHIJKLMNOPQRSTUVWXYZ "

def caractere_aleatorio():
    return random.choice(CARACTERES)

def frase_aleatoria(tamanho):
    # Etapa 1: Gera uma frase aleatória do mesmo tamanho da frase alvo
    return ''.join(caractere_aleatorio() for _ in range(tamanho))

def mutar(frase):
    # Etapa 3: Aplica mutações em cada caractere da frase, com 5% de chance
    return ''.join(
        caractere_aleatorio() if random.random() < TAXA_MUTACAO else c
        for c in frase
    )

def pontuacao(frase):
    # Etapa 4: Pontua cada cópia comparando com a frase alvo
    return sum(1 for a, b in zip(frase, FRASE_ALVO) if a == b)

def main():
    # Etapa 1: Gera a frase inicial aleatória
    frase = frase_aleatoria(len(FRASE_ALVO))
    geracao = 0

    while True:
        geracao += 1
        # Etapa 2: Cria 100 cópias da frase (com mutações)
        populacao = [mutar(frase) for _ in range(TAMANHO_POPULACAO)]
        # Etapa 4: Pontua cada cópia
        pontuacoes = [pontuacao(f) for f in populacao]
        # Etapa 5: Seleciona a melhor cópia para próxima geração
        melhor_pontuacao = max(pontuacoes)
        melhor_frase = populacao[pontuacoes.index(melhor_pontuacao)]

        print(f"Geração {geracao}: {melhor_frase} (Pontuação: {melhor_pontuacao})")

        # Etapa 6: Verifica se encontrou a frase alvo
        if melhor_pontuacao == len(FRASE_ALVO):
            print(f"Frase alvo encontrada em {geracao} gerações!")
            break

        # Etapa 5: Usa a melhor frase como base para próxima geração
        frase = melhor_frase

if __name__ == "__main__":
    main()