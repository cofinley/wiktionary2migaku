import re
import mmap
from abc import ABC, abstractmethod
from typing import Iterable, Match, Tuple

import wikitextparser as wtp

PAGE_REGEX = re.compile(rb"<page>.*?<title>(?P<title>.*?)</title>.*?<text[^>]+>(?P<text>.*?)\s*</text>.*?</page>", re.MULTILINE | re.DOTALL)


class LanguagePairParser(ABC):
    """
    Parser that goes through a wiktionary dump of a certain language (L1) and
    extracts a certain language's terms (L2, target language).
    """
    target_language_code = None  # Wiktionary language code to look for
    term_pattern = None  # Regex to match terms in page

    def __init__(self, input_file_path):
        self.input_file_path = input_file_path
        self.term_regex = re.compile(self.term_pattern, flags=re.MULTILINE | re.IGNORECASE)

    def parse_dump(self) -> Iterable[Tuple[str, str]]:
        """
        Create a generator for each page's title and text tag contents in the dump
        """
        with open(self.input_file_path, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
                for match in PAGE_REGEX.finditer(m):
                    yield match['title'], match['text']

    def count_pages(self) -> int:
        """
        Count number of <page> tag
        Used for tqdm progress bar ETA estimation
        """
        with open(self.input_file_path, encoding='utf-8') as f:
            return sum(1 for line in f if line.strip() == '<page>')

    def parse_page(self, args: Tuple[bytes, bytes]) -> list[dict]:
        """
        Parse page into list of one or more terms
        :param args: tuple of title and text XML tag contents (in bytes)
        """
        # Unpickle now that we're in a subprocess
        title, text = args
        if not title or not text:
            return []
        return self.get_page_terms(title.decode('utf-8'), text.decode('utf-8'))

    def get_page_terms(self, title: str, text: str) -> list[dict]:
        """
        Get all terms on a <page>
        There can be multiple if a term has multiple meanings/parts of speech
        :param text: Text contents of a page
        :param title: Term title
        """
        terms = []
        for match in self.term_regex.finditer(text):
            definitions = self.get_definitions(match)
            if not definitions:
                continue
            terms.append({
                'term': self.replace_smart_quotes(title),
                'altterm': '',
                'pronunciation': self.get_ipa(match),
                'pos': self.get_pos(match),
                'definition': definitions,
            })
        return terms

    @staticmethod
    def replace_smart_quotes(text: str) -> str:
        replacements = {
            # Apostrophe/single quote
            0x2018: "'",
            0x2019: "'",
            # Double quotes
            0x201c: '"',
            0x201d: '"'
        }
        return text.translate(replacements)

    def parse_text(self, text: str) -> str:
        """
        Get plaintext version of wikicode
        """
        plain_text = wtp.parse(text).plain_text().strip()
        plain_text = self.replace_smart_quotes(plain_text)
        return plain_text

    @abstractmethod
    def get_ipa(self, term_match: Match) -> str:
        """
        From the term's regex match, extract the international phoenetic alphabet string
        """
        pass

    @abstractmethod
    def get_pos(self, term_match: Match) -> str:
        """
        From the term's regex match, extract the part of speech (e.g. noun, verb)
        """
        pass

    @abstractmethod
    def get_definitions(self, term_match: Match) -> str:
        """
        From the term's regex match, extract the definitions
        """
        pass
