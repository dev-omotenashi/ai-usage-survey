"""
AI活用アンケートデータの処理・集計モジュール
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
from config import *


class AIUsageSurveyProcessor:
    def __init__(self, data_path=DATA_PATH):
        self.data_path = data_path
        self.df = None
        self.processed_data = {}
        
    def load_data(self):
        """TSVファイルを読み込み、基本的な前処理を行う"""
        self.df = pd.read_csv(self.data_path, sep='\t', encoding='utf-8')
        
        # タイムスタンプを datetime 型に変換
        self.df['タイムスタンプ'] = pd.to_datetime(self.df['タイムスタンプ'])
        
        # 年月列は既にデータに存在するので、そのまま使用
        # 年月列の形式を確認し、必要に応じて調整
        if '年月' in self.df.columns:
            # すでに年月列が存在する場合はそのまま使用
            pass
        else:
            # 年月列がない場合はタイムスタンプから生成
            self.df['年月'] = self.df['タイムスタンプ'].dt.strftime('%Y年%m月')
        
        return self.df
    
    def process_frequency_data(self):
        """利用頻度データを処理"""
        # 上流工程のツール利用頻度
        upstream_freq = {}
        for tool in UPSTREAM_TOOLS:
            col_name = f'先月で、上流工程の作業において、以下のAIツールをどのくらいの頻度で利用しましたか？ [{tool}]'
            if col_name in self.df.columns:
                freq_data = self.df.groupby(['年月', 'あなたが所属するチームはどちらですか？'])[col_name].apply(
                    lambda x: x.map(FREQUENCY_MAP).mean()
                ).reset_index()
                upstream_freq[tool] = freq_data
        
        # 開発工程のツール利用頻度
        dev_freq = {}
        for tool in DEVELOPMENT_TOOLS:
            col_name = f'先月、開発工程の作業において、以下のAIツールをどのくらいの頻度で利用しましたか？ [{tool}]'
            if col_name in self.df.columns:
                freq_data = self.df.groupby(['年月', 'あなたが所属するチームはどちらですか？'])[col_name].apply(
                    lambda x: x.map(FREQUENCY_MAP).mean()
                ).reset_index()
                dev_freq[tool] = freq_data
        
        self.processed_data['upstream_frequency'] = upstream_freq
        self.processed_data['development_frequency'] = dev_freq
        
    def process_contribution_data(self):
        """貢献度データを処理"""
        # 上流工程の貢献度
        upstream_contrib = {}
        for tool in UPSTREAM_TOOLS:
            col_name = f'上流工程の作業において、それぞれのAIツールは担当された作業の生産性向上にどの程度貢献したと感じますか？ [{tool}]'
            if col_name in self.df.columns:
                contrib_data = self.df.groupby(['年月', 'あなたが所属するチームはどちらですか？'])[col_name].apply(
                    lambda x: x.map(CONTRIBUTION_MAP).mean()
                ).reset_index()
                upstream_contrib[tool] = contrib_data
        
        # 開発工程の貢献度
        dev_contrib = {}
        for tool in DEVELOPMENT_TOOLS:
            col_name = f'開発工程の作業において、それぞれのAIツールは担当された作業の生産性向上にどの程度貢献したと感じますか？ [{tool}]'
            if col_name in self.df.columns:
                contrib_data = self.df.groupby(['年月', 'あなたが所属するチームはどちらですか？'])[col_name].apply(
                    lambda x: x.map(CONTRIBUTION_MAP).mean()
                ).reset_index()
                dev_contrib[tool] = contrib_data
        
        self.processed_data['upstream_contribution'] = upstream_contrib
        self.processed_data['development_contribution'] = dev_contrib
    
    def process_time_reduction_data(self):
        """時間削減効果データを処理"""
        # 上流工程の時間削減効果
        upstream_tasks = [
            '企画・提案の骨子検討',
            '提案資料作成',
            '仕様・要件整理（UI含む）',
            '概要設計・システム構成検討',
            'プレゼン・説明内容の整理',
            '事務作業',
            'その他'
        ]
        
        upstream_time = {}
        for task in upstream_tasks:
            col_name = f'上流工程において、AIツールを活用することで、担当作業について、おおよそどの程度の時間や労力が削減できたと感じますか？ [{task}]'
            if col_name in self.df.columns:
                time_data = self.df.groupby(['年月', 'あなたが所属するチームはどちらですか？'])[col_name].apply(
                    lambda x: x.map(TIME_REDUCTION_MAP).mean()
                ).reset_index()
                upstream_time[task] = time_data
        
        # 開発工程の時間削減効果
        dev_tasks = [
            '技術的な調査、問題解決のための情報収集',
            '設計作業（検討・整理含む）',
            'コーディング作業',
            '単体テスト作業（テストケース作成・実行）',
            'レビュー（コードや設計）',
            'その他'
        ]
        
        dev_time = {}
        for task in dev_tasks:
            col_name = f'開発工程において、AIツールを活用することで、おおよそどの程度の時間や労力が削減できたと感じますか？（可能な範囲で、具体的な作業とともにご記入ください） [{task}]'
            if col_name in self.df.columns:
                time_data = self.df.groupby(['年月', 'あなたが所属するチームはどちらですか？'])[col_name].apply(
                    lambda x: x.map(TIME_REDUCTION_MAP).mean()
                ).reset_index()
                dev_time[task] = time_data
        
        self.processed_data['upstream_time_reduction'] = upstream_time
        self.processed_data['development_time_reduction'] = dev_time
    
    def process_challenges(self):
        """課題データを処理（月別分析付き）"""
        # 上流工程の課題（全体）
        upstream_challenges_col = '上流工程でAIツールを活用する上で、どのような課題を感じていますか？（複数選択可）'
        if upstream_challenges_col in self.df.columns:
            challenges = []
            for idx, row in self.df.iterrows():
                if pd.notna(row[upstream_challenges_col]):
                    challenges.extend([c.strip() for c in str(row[upstream_challenges_col]).split(',')])
            
            challenge_counts = pd.Series(challenges).value_counts()
            self.processed_data['upstream_challenges'] = challenge_counts
        
        # 開発工程の課題（全体）
        dev_challenges_col = '開発工程でAIツールを活用する上で、どのような課題を感じていますか？（複数選択可）'
        if dev_challenges_col in self.df.columns:
            challenges = []
            for idx, row in self.df.iterrows():
                if pd.notna(row[dev_challenges_col]):
                    challenges.extend([c.strip() for c in str(row[dev_challenges_col]).split(',')])
            
            challenge_counts = pd.Series(challenges).value_counts()
            self.processed_data['development_challenges'] = challenge_counts
        
        # 月別課題分析
        self._process_monthly_challenges()
    
    def _process_monthly_challenges(self):
        """月別課題データを処理"""
        # 上流工程の月別課題
        upstream_challenges_col = '上流工程でAIツールを活用する上で、どのような課題を感じていますか？（複数選択可）'
        dev_challenges_col = '開発工程でAIツールを活用する上で、どのような課題を感じていますか？（複数選択可）'
        
        monthly_data = {}
        
        for month in ['2025年5月', '2025年6月', '2025年7月']:
            month_df = self.df[self.df['年月'] == month]
            monthly_data[month] = {}
            
            # 上流工程の課題
            if upstream_challenges_col in self.df.columns:
                upstream_team_data = month_df[month_df['あなたが所属するチームはどちらですか？'] == 'ディレクターチーム']
                challenges = []
                for idx, row in upstream_team_data.iterrows():
                    if pd.notna(row[upstream_challenges_col]):
                        challenges.extend([c.strip() for c in str(row[upstream_challenges_col]).split(',')])
                monthly_data[month]['upstream_challenges'] = pd.Series(challenges).value_counts() if challenges else pd.Series(dtype=int)
            
            # 開発工程の課題
            if dev_challenges_col in self.df.columns:
                dev_team_data = month_df[month_df['あなたが所属するチームはどちらですか？'] == 'エンジニアリングチーム']
                challenges = []
                for idx, row in dev_team_data.iterrows():
                    if pd.notna(row[dev_challenges_col]):
                        challenges.extend([c.strip() for c in str(row[dev_challenges_col]).split(',')])
                monthly_data[month]['development_challenges'] = pd.Series(challenges).value_counts() if challenges else pd.Series(dtype=int)
        
        self.processed_data['monthly_challenges'] = monthly_data
    
    def process_training_needs(self):
        """トレーニング・学習ニーズを処理（月別分析付き）"""
        training_col = 'AIツールをより効果的に活用するために、どのようなトレーニングや情報共有があると役立ちますか？（複数選択可）'
        if training_col in self.df.columns:
            training_needs = []
            for idx, row in self.df.iterrows():
                if pd.notna(row[training_col]):
                    training_needs.extend([t.strip() for t in str(row[training_col]).split(',')])
            
            training_counts = pd.Series(training_needs).value_counts()
            self.processed_data['training_needs'] = training_counts
        
        # 月別トレーニングニーズ分析
        self._process_monthly_training_needs()
    
    def _process_monthly_training_needs(self):
        """月別トレーニングニーズを処理"""
        training_col = 'AIツールをより効果的に活用するために、どのようなトレーニングや情報共有があると役立ちますか？（複数選択可）'
        
        monthly_data = {}
        
        for month in ['2025年5月', '2025年6月', '2025年7月']:
            month_df = self.df[self.df['年月'] == month]
            
            training_needs = []
            for idx, row in month_df.iterrows():
                if pd.notna(row[training_col]):
                    training_needs.extend([t.strip() for t in str(row[training_col]).split(',')])
            
            monthly_data[month] = pd.Series(training_needs).value_counts() if training_needs else pd.Series(dtype=int)
        
        self.processed_data['monthly_training_needs'] = monthly_data
    
    def process_text_feedback(self):
        """自由記述のフィードバックを処理"""
        feedback_cols = [
            '上流工程でAIツールを活用したことで、特に効果を実感した作業や具体的なエピソードがあれば教えてください。',
            'AIを活用した開発プロセス全体に関して、その他何か意見や要望があれば自由にご記入ください。'
        ]
        
        all_feedback = []
        for col in feedback_cols:
            if col in self.df.columns:
                feedback = self.df[col].dropna().tolist()
                all_feedback.extend(feedback)
        
        self.processed_data['feedback'] = all_feedback
    
    def save_processed_data(self):
        """処理済みデータを保存"""
        os.makedirs(PROCESSED_DATA_PATH, exist_ok=True)
        
        # DataFrameを保存
        for key, data in self.processed_data.items():
            if isinstance(data, dict):
                for tool, df in data.items():
                    if isinstance(df, pd.DataFrame):
                        filename = f"{key}_{tool.replace('/', '_').replace(' ', '_')}.csv"
                        df.to_csv(os.path.join(PROCESSED_DATA_PATH, filename), index=False)
            elif isinstance(data, pd.Series):
                filename = f"{key}.csv"
                data.to_csv(os.path.join(PROCESSED_DATA_PATH, filename))
    
    def process_all(self):
        """全ての処理を実行"""
        print("データを読み込んでいます...")
        self.load_data()
        
        print("利用頻度データを処理しています...")
        self.process_frequency_data()
        
        print("貢献度データを処理しています...")
        self.process_contribution_data()
        
        print("時間削減効果データを処理しています...")
        self.process_time_reduction_data()
        
        print("課題データを処理しています...")
        self.process_challenges()
        
        print("トレーニング・学習ニーズを処理しています...")
        self.process_training_needs()
        
        print("フィードバックを処理しています...")
        self.process_text_feedback()
        
        print("処理済みデータを保存しています...")
        self.save_processed_data()
        
        print("データ処理が完了しました。")
        return self.processed_data


if __name__ == "__main__":
    processor = AIUsageSurveyProcessor()
    processor.process_all()