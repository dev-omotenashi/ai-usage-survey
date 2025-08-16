"""
AI活用アンケート分析ダッシュボード設定ファイル
"""

DATA_PATH = '../data/AI活用アンケートデータ.tsv'
PROCESSED_DATA_PATH = '../data/processed/'

TEAM_NAMES = {
    'エンジニアリングチーム': 'Engineering',
    'ディレクターチーム': 'Director'
}

FREQUENCY_MAP = {
    '毎日': 5,
    '週に数回': 4,
    '月に数回': 3,
    'ほとんど利用しない': 2,
    '利用したことがない': 1,
    '': 0
}

CONTRIBUTION_MAP = {
    '5:非常に貢献した': 5,
    '4:貢献した': 4,
    '3:どちらともいえない': 3,
    '2:あまり貢献しなかった': 2,
    '1:全く貢献しなかった': 1,
    '利用していない/判断できない': 0,
    '': 0
}

TIME_REDUCTION_MAP = {
    '100%（依頼してほぼ終わり）': 100,
    '50%以上': 75,
    '30-50%程度': 40,
    '10-20%程度': 15,
    'あまり変わらない': 0,
    'むしろ増えてしまった': -10,
    '': None
}

UPSTREAM_TOOLS = [
    'ChatGPT',
    'Gemini',
    'genspark',
    'bolt.new',
    'Notebook LM',
    'Devin Search',
    'その他のAIツール'
]

DEVELOPMENT_TOOLS = [
    'ChatGPT / Gemini / Claude（会話）',
    'ChatGPT / Gemini / Claude（コーディング）',
    'Devin (Session / Search / wiki)',
    'GitHub Copilot',
    'Cursor',
    'Claude (ClaudeCode)',
    'その他'
]

# 表示用の短縮ラベル
TOOL_DISPLAY_NAMES = {
    'ChatGPT / Gemini / Claude（会話）': '汎用AI（会話）',
    'ChatGPT / Gemini / Claude（コーディング）': '汎用AI（コーディング）',
    'Devin (Session / Search / wiki)': 'Devin',
    'GitHub Copilot': 'GitHub Copilot',
    'Cursor': 'Cursor',
    'Claude (ClaudeCode)': 'Claude Code',
    'その他': 'その他',
    # 上流工程のツールはそのまま
    'ChatGPT': 'ChatGPT',
    'Gemini': 'Gemini',
    'genspark': 'genspark',
    'bolt.new': 'bolt.new',
    'Notebook LM': 'Notebook LM',
    'Devin Search': 'Devin Search',
    'その他のAIツール': 'その他のAIツール'
}