import os
import unittest

from language_parsers._language_pair_parser import LanguagePairParser
from language_parsers.fr_fr import French2French

PROJECT_DIR = os.path.dirname(__file__)
FIXTURES_DIR = os.path.join(PROJECT_DIR, 'fixtures')

class ParserTest(unittest.TestCase):
    def _parse_file(self, parser: LanguagePairParser, input_filename: str):
        """
        Test helper to simulate the multiprocessing flow
        """
        terms = []
        for page in parser.parse_dump():
            page_terms = parser.parse_page(page)
            terms += page_terms
        return terms

    def test_parser_parses_single_noun_xml_into_correct_json(self):
        input_filename = os.path.join(FIXTURES_DIR, 'single_noun.xml')
        p = French2French(input_filename)
        expected = [
            {
                'term': 'accueil',
                'altterm': '',
                'pronunciation': 'a.kœj',
                'pos': 'nom',
                'definition': "1. Cérémonie ou prestation réservée à un nouvel arrivant, consistant généralement à lui souhaiter la bienvenue et à l'aider dans son intégration ou ses démarches.\n2. Lieu où sont accueillies les personnes.\n3. (vieilli) Fait d'accueillir ou héberger.\n4. Page d'accès ou d'accueil (lieu ci-dessus) à un site web.\n5. Manière dont une œuvre a été acceptée lors de sa sortie par le public et les critiques.",
            }
        ]
        actual = self._parse_file(p, input_filename)
        self.assertDictEqual(expected[0], actual[0])

    def test_parser_parses_single_noun_xml_with_out_of_order_images_into_correct_json(self):
        input_filename = os.path.join(FIXTURES_DIR, 'single_noun_out_of_order_images.xml')
        p = French2French(input_filename)
        expected = [
            {
                'term': 'travaux',
                'altterm': '',
                'pronunciation': 'tʁa.vo',
                'pos': 'nom',
                'definition': "1. Pluriel de travail : Suite d'études, d'opérations, d'entreprises, pour élaborer, construire, édifier, quelque chose.\n2. Chantier.\n3. Désigne l'ensemble des résultats obtenus par un scientifique.\n4. Opérations sylvicoles nécessitant un investissement, des dépenses nettes.",
            }
        ]
        actual = self._parse_file(p, input_filename)
        self.assertDictEqual(expected[0], actual[0])

    def test_parser_parses_definitions_at_end_of_tag_correctly(self):
        # Newline after definition block in previous regex was expected instead of optional
        input_filename = os.path.join(FIXTURES_DIR, 'definitions_at_end_of_tag.xml')
        p = French2French(input_filename)
        expected = [
            {
                'term': 'constats',
                'altterm': '',
                'pronunciation': 'kɔ̃s.ta',
                'pos': 'nom',
                'definition': "1. Pluriel de constat.",
            }
        ]
        actual = self._parse_file(p, input_filename)
        self.assertDictEqual(expected[0], actual[0])

    def test_parser_parses_multiple_pos_for_same_word_correctly(self):
        # Multiple parts of speech on same page
        input_filename = os.path.join(FIXTURES_DIR, 'multiple_pos.xml')
        p = French2French(input_filename)
        expected = [
            {
                "term": "droite",
                "altterm": "",
                "pronunciation": "dʁwat",
                "pos": "nom",
                "definition": "1. Côté droit.\n2. Voie à droite du conducteur.\n3. (ellipse) Main droite.\n4. Coup donné avec la main.\n5. Terme regroupant divers courants politiques manifestant un attachement à la liberté, à l'ordre, considéré comme juste ou comme un moindre mal, réprouvant les changements brusques sur les questions de société et les questions éthiques, ainsi nommé parce qu'il s'est principalement manifesté à l'origine par les partis conservateurs ou réactionnaires qui siégeaient originellement (à partir de la Révolution) à droite du président de l'assemblée.\n6. Direction vers la fin d'une phrase.\n7. Trait résultant de la relation algébrique entre des variables, ellipse de ligne droite.\n8. Espace vectoriel de dimension un."
            },
            {
                "term": "droite",
                "altterm": "",
                "pronunciation": "dʁwat",
                "pos": "adjectif",
                "definition": "1. Féminin singulier de droit."
            }
        ]
        actual = self._parse_file(p, input_filename)
        self.assertDictEqual(expected[0], actual[0])


    def test_extract_definitions_numbers_the_definitions(self):
        input_text = "# [[lieu|Lieu]] où sont accueillies les [[personne]]s.\n" \
            "# [[page|Page]] d’[[accès]] ou d’accueil (lieu ci-dessus) à un site [[web]]."

        expected = "1. Lieu où sont accueillies les personnes.\n" \
            "2. Page d'accès ou d'accueil (lieu ci-dessus) à un site web."

        input_filename = os.path.join(FIXTURES_DIR, 'single_noun.xml')
        p = French2French(input_filename)
        actual = p.get_definitions(input_text)
        self.assertEqual(expected, actual)

    def test_parse_text_removes_wikilinks(self):
        input_text = "[[lieu|Lieu]] où sont accueillies les [[personne]]s."
        expected = "Lieu où sont accueillies les personnes."
        input_filename = os.path.join(FIXTURES_DIR, 'single_noun.xml')
        p = French2French(input_filename)
        actual = p.parse_text(input_text)
        self.assertEqual(expected, actual)

    def test_extract_definitions_respects_grammar_notes(self):
        input_text = "# {{vieilli|fr}} Fait d’[[accueillir]] ou [[héberger]]."
        expected = "1. (vieilli) Fait d'accueillir ou héberger."

        input_filename = os.path.join(FIXTURES_DIR, 'single_noun.xml')
        p = French2French(input_filename)
        actual = p.get_definitions(input_text)
        self.assertEqual(expected, actual)
