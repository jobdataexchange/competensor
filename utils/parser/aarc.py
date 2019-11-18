import pandas as pd

regex_for_area = r'(?P<area>^\w+\s\w+):' 
regex_for_uppercase_letters = r'(?P<letter>^[A-Z])\.'
regex_for_lowercase_letters = r'(?P<letter>^[a-z])\.'
regex_for_numbers = r'(?P<number>^\d)\.'
regex_for_text = r'[\.|:]\s(?P<text>.*)'


def break_into_alphanumeric_columns_and_forward_fill(file_path):
    df = pd.read_excel(file_path, header=None)
    df['area'] = df.iloc[:, 0].str.extract(regex_for_area)
    df['uppercase'] = df.iloc[:, 0].str.extract(regex_for_uppercase_letters)
    df['lowercase'] = df.iloc[:, 0].str.extract(regex_for_lowercase_letters)
    df['numbers'] = df.iloc[:, 0].str.extract(regex_for_numbers)
    df['text'] = df.iloc[:, 0].str.extract(regex_for_text)

    df['area'].ffill(inplace=True)
    df['uppercase'].ffill(inplace=True)

    null_text = df['text'].isnull()
    df.loc[null_text, 'text'] = df[null_text].iloc[:, 0]
    df['text'].dropna(inplace=True)

    return df