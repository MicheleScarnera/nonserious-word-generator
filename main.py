from nswg_word_generator import WordGenerator

wg = WordGenerator(depth=8)

wg.train(corpus="wiki.txt")

for _ in range(200):
    print(wg.generate_word(length_limit=100, length_penalty=0, min_word_length=2, show_problems=True))