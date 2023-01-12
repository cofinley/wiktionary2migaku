# Wiktionary2Migaku

Turn wiktionary database dumps into dictionaries that [Migaku](https://www.migaku.io/tools-guides) accepts.

The parser uses regex and generators to quickly sift through the large database dumps.

## Note

Before continuing, check the [languages](./src/language_parsers) folder to see if your language is supported. This project was created for parsing the French Wiktionary and currently only supports that language. The editing standards may also be different and require different regex.

## Created Dictionaries

- [French](https://github.com/cofinley/wiktionary2migaku/releases/download/0.1.0/Wiktionary-French-Monolingual.zip)

## Installation

1. Get the database dump from [Wikimedia Downloads](https://dumps.wikimedia.org/backup-index.html)
    - Look for the filename that ends with `-pages-articles.xml.bz2`.
2. Extract the `.bz2` file somewhere
    - This should result in a nested folder with a large XML file
    - This project will work with any text file that contains wikicode
3. Setup the project:

```bash
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
```

## Usage

1. Get your target language code from [Wiktionary's List of Languages](https://en.wiktionary.org/wiki/Wiktionary:List_of_languages)
2. Run the program (`python run.py`) with the arguments listed below:

```
usage: run.py [-h] -l1 DUMP_LANGUAGE_CODE -l2 DEFINITION_LANGUAGE_CODE -i INPUT_FILE

Parse wiktionary dump into Migaku Dictionary Format

optional arguments:
  -h, --help            show this help message and exit
  -l1 DUMP_LANGUAGE_CODE, --dump-language-code DUMP_LANGUAGE_CODE
                        Language code of the dump file (e.g. en, es, fr)
  -l2 DEFINITION_LANGUAGE_CODE, --definition-language-code DEFINITION_LANGUAGE_CODE
                        Language code of the definitions to get within the dump (e.g. en, es, fr)
  -i INPUT_FILE, --input-file INPUT_FILE
                        Absolute file path of input text file to parse
```

### Adding Languages

You can add your own language parsers which can handle any combination of dump file languages and which language's definitions you wish to parse from the dump file. Not all wiktionary language pages abide by the same formatting, so regexes that work in one dump file may not work in another. You'll need to tweak the regexes for finding terms, their IPA, their definitions, and their part of speech.

1. Add a new python file under `src/language_parsers` with language pair as name
    - Language pair format = `f'{dump_language_code}_{definition_language_code}'`
    - e.g. `fr_fr.py` for French definitions in a French dump file
1. Create a class in that file with the format `f'{dump_language_name}2{definition_language_name}'`
    - e.g. `French2French` for French definitions in a French dump file
    - Inherit from `language_parsers._language_pair_parser.LanguagePairParser`
1. Override class' `term_regex` which finds each term section
1. Override abstract methods `get_ipa()`, `get_pos()`, and `get_definitions()`
1. Add parser to `src/language_parsers/__init__.py` under `LANGUAGE_PAIR_PARSERS`
    - Import the parser above, map the short pair name (e.g. fr_fr) to the class
1. Run the python script, `run.py` with `-l1/--dump-language-code` with the dump language code that matches the first part of the mapping and `-l2/--definition-language-code` with the definition language code that matches the second part of the mapping

### Example

Say I want to create a parser that gets Spanish words from the English wiktionary dump (i.e. bilingual definitions). This could be considered EN->ES. I would:

1. Add `en_es.py` under `src/language_parsers`
1. Add class `English2Spanish` and inherit from `LanguagePairParser`
1. Add logic specific to this language pair
1. Add `'en_es': English2Spanish` in `LANGUAGE_PAIR_PARSERS`
1. Run script with `python run.py -l1 en -l2 es -i <absolute path to english wiktionary dump>`

## Tests

```
python -m unittest [discover]
```
