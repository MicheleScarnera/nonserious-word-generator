import numpy as np
import string
import nswg_utils
from time import time

end_character = "<end>"

class WordGenerator:
    def __init__(self, depth=1):
        self.trained = False
        self.alphabet = list()
        self.distributions = dict()
        self.depth = depth

    def summary(self, max_depth=1):
        if self.depth <= max_depth:
            print("Summary of the distribution:")
            for key in self.distributions.keys():
                rounded_values = [f"{p}%" for p in nswg_utils.round_percentages(self.distributions[key] * 100)]
                print(f" - \'{key}\' -> {[f'{letter}: {percent}' for letter, percent in zip(self.alphabet, rounded_values)]};")
        else:
            print(f"Summary of the distribution has been omitted due to large depth ({self.depth}). To override this, change the max_depth parameter (currently {max_depth}).")

    def add_to_distribution(self, key, letter_seen):
        if key not in self.distributions:
            self.distributions[key] = np.zeros(shape=len(self.alphabet), dtype=np.float64)

        index = self.alphabet.index(letter_seen)
        self.distributions[key][index] = self.distributions[key][index] + 1

    def train(self, corpus=None, verbose=0):
        if self.trained:
            raise Exception("Word generator already trained")

        if corpus is None:
            print("Corpus was not given. Getting TensorFlow's shakespeare.txt...")
            corpus = 'shakespeare.txt'

        # clean dataset
        with open(corpus, errors="replace") as f:
            words = f.read()

        # remove punctuation
        words = words.translate(str.maketrans('', '', string.punctuation))

        # remove numbers
        words = words.translate(str.maketrans('', '', "0123456789"))

        # make it all lowercase
        words = words.lower()

        # make other nasty characters easily identifiable
        easily_identifiable = '#'
        for nasty in (' ', '\n', '\t'):
            words = words.replace(nasty, easily_identifiable)

        # use easily_identifiable as a marker to split
        words = words.split(easily_identifiable)

        words = np.unique([word for word in words if word != ''])

        print(f"{len(words)} words that will be used to train: {words}")

        print("Getting alphabet...")

        s = set()
        for word in words:
            for letter in word:
                s.add(letter)

        self.alphabet = sorted(list(s))
        s = None

        # append end_character at the end of the alphabet
        self.alphabet.append(end_character)

        print(f"Alphabet: {self.alphabet}")

        # commence training
        trainingtext = "Training..."
        W = len(words)
        start = time()
        print(trainingtext, end='\r')

        for w, word in enumerate(words):
            if verbose > 1:
                print(f"Word: {word}:")

            word_appended = word + '\r'
            for l, letter in enumerate(word_appended):
                if l == 0:
                    # 'first letter' distribution
                    self.add_to_distribution('', letter)
                else:
                    # P(letter|previous_letters)
                    for d in range(1, np.min([self.depth, l]) + 1):
                        previous_letters = word[l - d:l]
                        if verbose > 1:
                            print(f"    previous_letters: {previous_letters}, letter: {letter}")

                        if letter != '\r':
                            self.add_to_distribution(previous_letters, letter)
                        else:
                            # 'end character' distribution
                            self.add_to_distribution(previous_letters, end_character)

            beginch = '\r'
            endch = ''
            if w == W - 1:
                endch = '\n'

            if (w == W - 1) or (w % 500 == 0):
                w_ = w+1
                end = time()
                average_time = (end - start) / w_
                eta = int((average_time * (W - w_)))

                print(f"{beginch}{trainingtext} {w_/W:.1%} ETA: {nswg_utils.timeformat(eta)}", end=endch)

        # normalize
        for key in self.distributions.keys():
            value = self.distributions[key]
            self.distributions[key] = value / np.sum(value)

        self.trained = True

        self.summary()
        
    def generate_word(self, length_limit=30, length_penalty=0, reroll_short_words_threshold=2, show_problems=True, verbose=0):
        problems = []
        while True:
            result = ''
            new_character = ''

            # at the occurrence, we limit the information the generator has access to,
            # making it behave as if the word generation just began
            safe_index = 0

            while len(result) < length_limit:
                if result != '':
                    l = len(result)

                    for d in reversed(range(1, np.min([self.depth, l]) + 1)):
                        information = result[np.max([l - d, safe_index]):l]
                        if verbose > 1:
                            print(f"Information is {information} (Depth {d})")

                        try:
                            dist = self.distributions[information]

                            break
                        except KeyError:
                            if d > 1:
                                problems.append("deadend-minor")
                                continue
                            else:
                                dist = self.distributions['']
                                safe_index = l
                                problems.append("deadend-major")

                                if verbose > 1:
                                    print(f"(Dead end)")
                else:
                    dist = self.distributions['']

                # apply length penalty
                if length_penalty > 0:
                    dist[-1] = dist[-1] + len(result) * length_penalty
                    dist = dist / np.sum(dist)

                new_character = np.random.choice(a=self.alphabet, size=1, replace=True, p=dist)[0]

                if verbose > 1:
                    print(f"New character: {new_character}")

                if new_character == end_character:
                    break

                result = f"{result}{new_character}"
                #print(result)

            if len(result) <= reroll_short_words_threshold:
                problems.append("reroll")
                continue

            if len(result) == length_limit:
                problems.append("lengthlimit")

            if show_problems and len(problems) > 0:
                return f"{result} ({nswg_utils.print_list_with_duplicates(problems)})"
            else:
                return result

wg = WordGenerator(depth=8)

wg.train("wiki.txt")

for _ in range(100):
    print(wg.generate_word(length_limit=100, length_penalty=0))
