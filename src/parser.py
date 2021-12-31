import re
import mmap
from typing import Optional, Match

import wikitextparser as wtp


class Parser:
    def __init__(self, language_code: str, input_filename: str):
        self.language_code = language_code
        self.language = self.get_language()
        self.input_filename = input_filename
        # Terms
        self.TERM_PATTERN = r"(?P<word_template>^=== {{S\|(?P<word_type>" + '|'.join(self.language.WORD_TYPES) + ")\|" + self.language_code + "(?:\||}}).*)(?:.*\n)+?(?P<title_group>^'''.*\n)(?P<defs>(?:^#.*\n)*)"
        # Break apart title line ('''...''' ...)
        self.TITLE_LINE_PATTERN = r"^'''(?P<title>.+)(?=''')'''\s?(?:{{pron\|(?P<ipa>[^|]*)\|[^}]+}}(?P<rest>.*))?"
        # Definition line
        self.DEFINITION_PATTERN = r"^#\s?(?:{{(?P<grammar>[^|}]+)(?:\|\w+)?}}\s?)?(?P<rest>.*)"

    def get_language(self):
        if self.language_code == 'fr':
            from languages.fr import French
            return French

    def count_terms(self):
        pattern = re.compile(bytes(self.TERM_PATTERN, encoding='utf-8'), re.MULTILINE | re.IGNORECASE)
        with open(self.input_filename, 'r') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
                return len(tuple(pattern.finditer(m)))

    def parse(self):
        pattern = re.compile(bytes(self.TERM_PATTERN, encoding='utf-8'), re.MULTILINE | re.IGNORECASE)
        with open(self.input_filename, 'r') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
                for i, match in enumerate(pattern.finditer(m)):
                    term = self.parse_match(match)
                    if not term:
                        continue
                    term['id'] = i
                    yield term

    def parse_match(self, match: Match) -> Optional[dict]:
        if not self.is_valid_mot(match['word_template']):
            return None
        title_group = match['title_group']
        word_type = match['word_type']
        defs = match['defs']
        title, ipa, rest = self.parse_title_group(title_group)
        if not title:
            return None
        definitions = self.extract_definitions(defs)
        return {
            'term': title,
            'altterm': '',
            'pronunciation': ipa,
            'pos': word_type,
            'definition': definitions,
            'examples': '',
            'audio': ''
        }

    @staticmethod
    def is_valid_mot(word_template: str) -> bool:
        return bool(re.search(rb'\|fr(?:\||}})', word_template))

    @staticmethod
    def parse_text(text: str) -> str:
        plain_text = wtp.parse(text).plain_text().strip()
        return plain_text.replace("’", "'")

    def parse_title_group(self, title_group: str):
        pattern = re.compile(bytes(self.TITLE_LINE_PATTERN, encoding='utf-8'))
        match = pattern.search(title_group)
        if match is None or match['title'] is None:
            return '', '', ''
        return match['title'], match['ipa'] or '', match['rest'] or ''

    def extract_definitions(self, defs: str) -> str:
        if type(defs) is bytes:
            defs = defs.decode('utf-8')
        if defs == '':
            return ''
        definitions = []
        def_list = wtp.parse(defs).get_lists()[0]
        for i, definition in enumerate(def_list.fullitems):
            match = re.search(self.DEFINITION_PATTERN, definition)
            grammar_type = match['grammar']
            rest = match['rest']
            plain_text = self.parse_text(rest)
            d = str(i+1) + '.'
            if grammar_type and grammar_type.lower() in self.language.GRAMMAR_TYPES:
                d += f' ({grammar_type})'
            d += f' {plain_text}'
            definitions.append(d)
        return '\n'.join(definitions)
