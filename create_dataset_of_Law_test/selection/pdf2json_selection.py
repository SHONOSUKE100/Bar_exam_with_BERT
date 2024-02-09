import re
from PyPDF2 import PdfReader
import camelot
import pandas as pd
import json
import itertools

def extract_questions_from_text(path):
    # PDFファイルを読み込み
    reader = PdfReader(path)
    patterns = [r'\n', r'\r', r'-\d{1,2}-', r'-\d\s\d-']
    number_of_pages = len(reader.pages)
    all_text = ''
    for i in range(number_of_pages):
        text = reader.pages[i].extract_text()
        # 正規表現にマッチする部分を抽出
        matches = []
        for pattern in patterns:
            matches.extend(re.findall(pattern, text))  
        text = re.sub('|'.join(patterns), '', text)
        all_text += text
    # 正規表現パターンを修正して、「（配点：２）」の部分を除去
    pattern = r"〔第(\d+)問〕(.*?)(?=〔第\d+問〕|\Z)"

    # テキストから問題を抽出
    matches = re.findall(pattern, all_text, re.DOTALL)

    # JSON形式に整形
    questions_json = {"questions" : []}

    for num, content in matches:
        cleaned_content = re.sub(r'（配点：\d）', "", content).strip()
        cleaned_content = re.sub(r'\[№\d+\]', "", cleaned_content).strip()
        cleaned_content = re.sub(r'№\d+', "", cleaned_content).strip()
        questions_json["questions"].append({"num": int(num), "question": cleaned_content})


    return questions_json

def extract_answers_from_pdf(path):
    tables = camelot.read_pdf(path, pages="all")
    df = tables[0].df
    df.columns = df.iloc[0]
    df = df.drop(0)
    total_columns = df.shape[1]

    column_nums = total_columns // 5
    split_index = total_columns // column_nums

    # 列数に応じてDataFrameを分割する処理を一般化
    dfs = [df.iloc[:, i*split_index:(i+1)*split_index].reset_index(drop=True) for i in range(column_nums)]
    for df_part in dfs:
        df_part.columns = ['Num', 'num', 'answer', 'point', 'notion']

    df_clean = pd.concat(dfs, axis=0).reset_index(drop=True)
    for row in range(len(df_clean.iloc[:, 0])):
        if df_clean.iloc[row, 0] == "":
            df_clean.iloc[row, 0] = df_clean.iloc[row-1, 0]

    # Specify the column numbers to include in the JSON
    column1 = 0
    column2 = 2
    column3 = 4
    # Create a new dataframe with the selected columns
    selected_columns = df_clean.iloc[:, [column1, column2, column3]]

    selected_columns.columns = ["num_problem", "answer", "Notion"]

    drop_index = selected_columns[selected_columns['answer'] == ""].index
    df_clean = selected_columns.drop(drop_index).reset_index(drop=True)

    df_clean['num_problem'] = df_clean['num_problem'].astype(int)


    # num_problem ごとに answer を結合し、Notion 列が '順'、'不'、'同' をそれぞれ含むかどうかをチェック
    grouped = df_clean.groupby('num_problem').agg({
        'answer': lambda x: ', '.join(x),
        'Notion': lambda x: any(
            ('順' in notion) and ('不' in notion) and ('同' in notion) for notion in x
        )
    }).reset_index()

    # Converting to JSON format
    json_dict = grouped.to_dict(orient='records')

    # Formatting the JSON output
    answers_json = {
        "answers": [
            {"num": str(item['num_problem']), "ans": item['answer'], "any_order": item['Notion']}
            for item in json_dict
        ]
    }
    return answers_json

def process_answers(answers_json):
    processed_answers = []

    for answer in answers_json["answers"]:
        num = answer['num']
        ans_text = answer['ans']
        any_order = answer['any_order']

        # 順不同の場合、全ての順列を生成
        if any_order:
            # カンマとスペースで分割して順列を生成
            ans_parts = ans_text.split(', ')
            permutations = itertools.permutations(ans_parts)
            all_combinations = [', '.join(permutation) for permutation in permutations]
        else:
            if "\n" in ans_text:
                    ans_text = ans_text.replace("\n", ", ")
            all_combinations = [ans_text]  # 順不同でない場合は元の回答を使用

        processed_answers.append({"num": num, "ans": all_combinations})
        answers_json_2 = {"answers": processed_answers}
    return answers_json_2

def connect_question_and_answer(question_json, answers_json_2):
    questions = question_json['questions']
    answers = answers_json_2['answers']
    connected_json = []

    for question in questions:
        for answer in answers:
            if str(question['num']) == answer['num']:
                # 回答リストの処理
                answer_texts = answer['ans']
                connected_json.append({"question_text": question['question'], "answers": answer_texts})

    return connected_json


def process_pairs(start_year, end_year, path):
    legal_questions_and_answer_dataset = {}
    for year in range(start_year, end_year+1):
        question_file = f"{path}/question_{year}.pdf"
        answer_file = f"{path}/answer_{year}.pdf"
        question_json = extract_questions_from_text(question_file)
        answer_json = extract_answers_from_pdf(answer_file)
        answer_json_2 = process_answers(answer_json)
        question_answer_pairs = connect_question_and_answer(question_json, answer_json_2)

        # 各質問に対して記述と選択肢を抽出
        for pair in question_answer_pairs:
            new_text = pair["question_text"]

            # 各記述を抽出する正規表現
            statements_pattern = r"\d．.+?(?=\d．|$)"

            # 各記述の抽出
            statements = re.sub(statements_pattern, "", new_text, re.DOTALL)
            choices = re.findall(statements_pattern, new_text, re.DOTALL)
            choices = [choice.lstrip('\d．').strip() for choice in choices]  # 改善された選択肢の抽出

            
            statements = statements.strip() if statements.strip() else "None"
            choices = choices if choices else ["None"]

            # 結果をpairに追加
            pair["question_body"] = statements
            pair["options"] = choices
        
        legal_questions_and_answer_dataset[str(year)] = question_answer_pairs
    
    return legal_questions_and_answer_dataset
