import unittest
from pdf2json_selection import extract_answers_from_pdf

class TestExtractAnswersFromPDF(unittest.TestCase):
    def test_extract_answers_from_pdf(self):
        # Test case 1: PDF with valid data
        path = "pdf_dataset/Civil_Law/answer_2011.pdf"
        expected_output = {
            "answers": [
                {"num": "1", "ans": "Answer 1"},
                {"num": "2", "ans": "Answer 2"},
                {"num": "3", "ans": "Answer 3"}
            ]
        }
        self.assertEqual(extract_answers_from_pdf(path), expected_output)

        # Test case 2: PDF with empty answers
        path = "pdf_dataset/Civil_Law/answer_2012.pdf"
        expected_output = {
            "answers": [
                {"num": "1", "ans": "Answer 1"},
                {"num": "3", "ans": "Answer 3"}
            ]
        }
        self.assertEqual(extract_answers_from_pdf(path), expected_output)

        # Test case 3: PDF with missing data
        path = "pdf_dataset/Civil_Law/answer_2013.pdf"
        expected_output = {
            "answers": [
                {"num": "1", "ans": "Answer 1"},
                {"num": "2", "ans": "Answer 2"},
                {"num": "3", "ans": "Answer 3"},
                {"num": "4", "ans": "Answer 4"}
            ]
        }
        self.assertEqual(extract_answers_from_pdf(path), expected_output)

if __name__ == '__main__':
    unittest.main()
