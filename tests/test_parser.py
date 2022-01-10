import os
import unittest

from parser import Parser

PROJECT_DIR = os.path.dirname(__file__)
FIXTURES_DIR = os.path.join(PROJECT_DIR, 'fixtures')

class ParserTest(unittest.TestCase):
    def test_parser_parses_single_noun_xml_into_correct_json(self):
        input_filename = os.path.join(FIXTURES_DIR, 'single_noun.xml')
        p = Parser('fr', input_filename)
        expected = [
            {
                'term': bytes('accueil', encoding='utf-8'),
                'altterm': '',
                'pronunciation': bytes('a.kœj', encoding='utf-8'),
                'pos': bytes('nom', encoding='utf-8'),
                'definition': "1. Cérémonie ou prestation réservée à un nouvel arrivant, consistant généralement à lui souhaiter la bienvenue et à l'aider dans son intégration ou ses démarches.\n2. Lieu où sont accueillies les personnes.\n3. (vieilli) Fait d'accueillir ou héberger.\n4. Page d'accès ou d'accueil (lieu ci-dessus) à un site web.\n5. Manière dont une œuvre a été acceptée lors de sa sortie par le public et les critiques.",
                'id': 0,
            }
        ]
        actual = list(p.parse())
        self.assertDictEqual(expected[0], actual[0])

    def test_parser_parses_single_noun_xml_with_out_of_order_images_into_correct_json(self):
        input_filename = os.path.join(FIXTURES_DIR, 'single_noun_out_of_order_images.xml')
        p = Parser('fr', input_filename)
        expected = [
            {
                'term': bytes('travaux', encoding='utf-8'),
                'altterm': '',
                'pronunciation': bytes('tʁa.vo', encoding='utf-8'),
                'pos': bytes('nom', encoding='utf-8'),
                'definition': "1. Pluriel de travail : Suite d'études, d'opérations, d'entreprises, pour élaborer, construire, édifier, quelque chose.\n2. Chantier.\n3. Désigne l'ensemble des résultats obtenus par un scientifique.\n4. Opérations sylvicoles nécessitant un investissement, des dépenses nettes.",
                'id': 0,
            }
        ]
        actual = list(p.parse())
        self.assertDictEqual(expected[0], actual[0])


    def test_extract_definitions_numbers_the_definitions(self):
        input_text = "# [[lieu|Lieu]] où sont accueillies les [[personne]]s.\n" \
            "# [[page|Page]] d’[[accès]] ou d’accueil (lieu ci-dessus) à un site [[web]]."

        expected = "1. Lieu où sont accueillies les personnes.\n" \
            "2. Page d'accès ou d'accueil (lieu ci-dessus) à un site web."

        input_filename = os.path.join(FIXTURES_DIR, 'single_noun.xml')
        p = Parser('fr', input_filename)
        actual = p.extract_definitions(input_text)
        self.assertEqual(expected, actual)

    def test_parse_text_removes_wikilinks(self):
        input_text = "[[lieu|Lieu]] où sont accueillies les [[personne]]s."
        expected = "Lieu où sont accueillies les personnes."
        input_filename = os.path.join(FIXTURES_DIR, 'single_noun.xml')
        p = Parser('fr', input_filename)
        actual = p.parse_text(input_text)
        self.assertEqual(expected, actual)

    def test_extract_definitions_respects_grammar_notes(self):
        input_text = "# {{vieilli|fr}} Fait d’[[accueillir]] ou [[héberger]]."
        expected = "1. (vieilli) Fait d'accueillir ou héberger."

        input_filename = os.path.join(FIXTURES_DIR, 'single_noun.xml')
        p = Parser('fr', input_filename)
        actual = p.extract_definitions(input_text)
        self.assertEqual(expected, actual)
