# nonserious-word-generator
Program that generates novel words using a 'quasi Markov Chain' approach.

It is written in `Python 3.10` and makes use of the `numpy` library.
 
Words are constructed one letter at a time, and each letter is chosen depending on (a window of) the letters that precede it. Under some settings, the generation process is exactly a Markov Chain.
 
**As the name of the program implies, this was not written to be of any serious use, and was mainly written to see if the outputs would be funny.**

# Corpora

Some corpora are included for convenience:

- `shakespeare.txt`, from TensorFlow
- `now.txt`, free sample lexicon from [corpusdata.org](https://www.corpusdata.org/intro.asp)
- `ger.txt`, german corpus from [Wortschatz Leipzig](https://wortschatz.uni-leipzig.de/)
- `span.txt`, free sample lexicon of the spanish corpus on [corpusdata.org](https://www.corpusdata.org/intro.asp)

If you wish to use your own data, all you need is a txt file with unstructured text. Individual words for training will be extracted automatically.

# Execution

Run `main.py`. Without any modification to that file, a word generator will be trained on `wiki.txt` and 200 words will be generated.

Check the comments in `nswg_word_generator.py` for an explanation of the parameters.