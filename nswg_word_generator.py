import numpy as np
import string
import nswg_utils
from time import time

end_character = "<end>"

class WordGenerator:
    def __init__(self, depth=1):
        """
        Initializes the word generator.

        :param depth: How many letters will the word generator take into account to generate the next letter. For depth=1, only the last letter will be considered (making this generator a Markov Chain), for depth=2, the last two, et cetera.
        """
        self.trained = False
        self.alphabet = list()
        self.distributions = dict()
        self.words = []
        self.depth = depth

    def summary(self, max_depth=1):
        """
        Prints a summary of the word generator.

        :param max_depth: If the generator has depth bigger than this amount, its sampling distribution will not be printed.
        :return: None
        """
        print(f"Word generator with depth {self.depth}")
        if self.trained > 0:
            if self.depth <= max_depth:
                print("Summary of the distribution:")
                for key in self.distributions.keys():
                    rounded_values = [f"{p}%" for p in nswg_utils.round_percentages(self.distributions[key] * 100)]
                    print(f" - \'{key}\' -> {[f'{letter}: {percent}' for letter, percent in zip(self.alphabet, rounded_values)]};")
            else:
                print(f"Summary of the distribution has been omitted due to large depth ({self.depth}). To override this, change the max_depth parameter (currently {max_depth}).")
        else:
            print("The word generator is not trained")

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
        else:
            print(f"Creating a word generator on {corpus}...")

        # clean dataset
        with open(corpus, errors="replace") as f:
            words = f.read()

        # remove punctuation
        print("Removing punctuation...")
        words = words.translate(str.maketrans('', '', string.punctuation))

        # remove numbers
        print("Removing numbers...")
        words = words.translate(str.maketrans('', '', "0123456789"))

        # make it all lowercase
        print("Making the corpus lowercase...")
        words = words.lower()

        # make other nasty characters easily identifiable
        print("Removing nasty characters...")
        easily_identifiable = '#'
        for nasty in ' \n\t??????????????????????+???????????????????????????????????????????????????????????????????????????????????':
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

        # shuffle words (should make ETAs more stable)
        shuffled_indices = np.array(range(0, len(words)))
        np.random.shuffle(shuffled_indices)

        # commence training
        trainingtext = "Training..."
        W = len(words)
        start = time()
        print(trainingtext, end='\r')

        for w, word in enumerate(words[shuffled_indices]):
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
                end = time()

                if w == W - 1:
                    secondpart = f"Took {nswg_utils.timeformat(end - start)}"
                else:
                    w_ = w + 1
                    average_time = (end - start) / w_
                    eta = int((average_time * (W - w_)))
                    secondpart = f"{w_ / W:.1%} [ETA: {nswg_utils.timeformat(eta)}]"

                print(f"{beginch}{trainingtext} {secondpart}", end=endch)

        # normalize
        start = time()
        normtext = "Normalizing..."
        K = len(self.distributions.keys())
        for k, key in enumerate(self.distributions.keys()):
            value = self.distributions[key]
            self.distributions[key] = value / np.sum(value)

            beginch = '\r'
            endch = ''
            if k == K - 1:
                endch = '\n'

            if (k == K - 1) or (k % 500 == 0):
                end = time()

                if k == K - 1:
                    secondpart = f"Took {nswg_utils.timeformat(end - start)}"
                else:
                    k_ = k + 1
                    average_time = (end - start) / k_
                    eta = int((average_time * (K - k_)))
                    secondpart = f"{k_ / K:.1%} [ETA: {nswg_utils.timeformat(eta)}]"

                print(f"{beginch}{normtext} {secondpart}", end=endch)

        self.trained = True

        # save words for later
        self.words = words

        self.summary()
        
    def generate_word(self, length_limit=30, length_penalty=0, min_word_length=2, show_problems=True, verbose=0):
        """
        Generate a word using a trained word generator.

        :param length_limit: The generation of the word will be halted when the word is length_limit characters long.

        :param length_penalty: (Unnecessary) Penalize word length by linearly increasing the probability of  terminating the word. The additional probabilty of the word halting due to this is (length_penalty * current length of the word).

        :param min_word_length: If the generated word is shorter than this, the generation will be rerolled.

        :param show_problems: Include in the output anything that went wrong in the generation (deadend, reroll, overfit)

        :param verbose: Level of verbosity. Mostly unused.
        :return: string
        """
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
                                # the word generator doesn't know what to do with the current information.
                                # depth will be reduced by 1 and the generator will try again
                                problems.append("deadend-minor")
                                continue
                            else:
                                # if the generator meets dead ends for every depth,
                                # the word will continue as if there is no prior information
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

            if len(result) <= min_word_length:
                problems.append("reroll")
                continue

            if len(result) == length_limit:
                problems.append("lengthlimit")

            # check if the word is overfit
            # binary searches where the generated word would be in the training set,
            # and if it finds a perfect match it's deemed overfit
            j = np.searchsorted(self.words, result)
            for s in [-1, 0, 1]:
                index = np.clip(j+s, 0, len(self.words) - 1)
                if self.words[index] == result:
                    problems.append("overfit")
                    break

            if show_problems and len(problems) > 0:
                return f"{result} ({nswg_utils.print_list_with_duplicates(problems)})"
            else:
                return result

