
import random

TARGET_PHRASE = "METHINKS IT IS LIKE A WEASEL"
POPULATION_SIZE = 100
MUTATION_RATE = 0.05
CHARACTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ "


def random_character():
    return random.choice(CHARACTERS)


def random_phrase(length):
    # Step 1: Generate a random phrase of the same length as the target
    return ''.join(random_character() for _ in range(length))


def mutate(phrase):
    # Step 3: Apply mutations to each character with 5% chance
    return ''.join(
        random_character() if random.random() < MUTATION_RATE else c
        for c in phrase
    )


def score(phrase):
    # Step 4: Score each copy by comparing with the target phrase
    return sum(1 for a, b in zip(phrase, TARGET_PHRASE) if a == b)


def main():
    # Step 1: Generate the initial random phrase
    phrase = random_phrase(len(TARGET_PHRASE))
    generation = 0

    while True:
        generation += 1
        # Step 2: Create 100 copies of the phrase (with mutations)
        population = [mutate(phrase) for _ in range(POPULATION_SIZE)]
        # Step 4: Score each copy
        scores = [score(p) for p in population]
        # Step 5: Select the best copy for the next generation
        best_score = max(scores)
        best_phrase = population[scores.index(best_score)]

        print(f"Generation {generation}: {best_phrase} (Score: {best_score})")

        # Step 6: Check if the target phrase was found
        if best_score == len(TARGET_PHRASE):
            print(f"Target phrase found in {generation} generations!")
            break

        # Step 5: Use the best phrase as the base for the next generation
        phrase = best_phrase

if __name__ == "__main__":
    main()