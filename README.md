# AI活用アンケート分析ダッシュボード

観光ビッグデータ事業部のAIツール活用状況を分析・可視化するStreamlitダッシュボードアプリケーション。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io)

## 🎯 概要

3ヶ月間（2025年5月〜7月）のAIツール活用アンケートデータを基に、チーム別の利用傾向と効果を総合的に分析します。

### 主な分析項目
- 📊 **利用頻度の推移**: 月別・ツール別の使用状況
- 💡 **生産性への貢献度**: 各ツールの効果測定
- ⏱️ **時間削減効果**: 作業別の効率化成果
- 📝 **課題とニーズ**: 活用における障壁と改善要望

### 対象チーム
- **上流工程**: ディレクターチーム（企画・提案・設計）
- **開発工程**: エンジニアリングチーム（実装・テスト）

## 🚀 クイックスタート

### 必要環境
- Python 3.11以上
- pip（パッケージマネージャー）

### インストールと起動

```bash
# リポジトリをクローン
git clone https://github.com/dev-omotenashi/ai-usage-survey.git
cd ai-usage-survey

# 依存パッケージをインストール
pip install streamlit pandas plotly wordcloud matplotlib

# ダッシュボードを起動
streamlit run src/dashboard.py
```

ブラウザで http://localhost:8501 にアクセスしてダッシュボードを確認できます。

## 📊 ダッシュボード機能

### 1. 📊 概要タブ
- **調査概要**: 背景・目的・対象ツールの説明
- **回答数サマリー**: チーム別・月別の回答状況
- **基本統計**: 総回答数と参加率の可視化

### 2. 📈 利用頻度・生産性分析タブ
- **指標カード**: 
  - 最も使用されたツール
  - 最高貢献度ツール
  - 総合スコア（頻度×貢献度）
  - 最も改善したツール
- **時系列推移**: 月別の利用頻度・貢献度グラフ
- **ヒートマップ**: 利用頻度×貢献度の組み合わせ分析
- **クロス集計表**: ツール別の詳細5×5分析

### 3. ⏱️ 時間削減効果タブ
- **指標カード**: 最高/最低削減効果、改善/悪化作業の特定
- **削減効果グラフ**: 上流・開発工程別の作業別削減率
- **月別推移**: 5月→7月の削減効果変化
- **具体的事例**: アコーディオン形式で実例を表示

### 4. 📝 課題・フィードバックタブ
- **月別比較表**: 課題・トレーニングニーズの変化分析
- **色分け表示**: 
  - 🔵 新規項目
  - 🟠 増加傾向  
  - 🟢 解消項目
  - 🔴 減少傾向
- **優先順位**: 7月の件数でソート表示

### サイドバー機能
- **調査情報パネル**: 期間・回答数・対象ツール等
- **ダッシュボードガイド**: 各タブの使い方説明
- **データ解釈ヒント**: 指標の読み方と活用ポイント

## 🏗️ プロジェクト構成

```
ai-usage-survey/
├── 📄 CLAUDE.md                     # 詳細技術仕様
├── 📄 README.md                     # このファイル  
├── 📂 data/
│   ├── 📊 AI活用アンケートデータ.tsv   # 元データ（TSV形式）
│   └── 📂 processed/                # 処理済みデータ保存用
└── 📂 src/
    ├── ⚙️ config.py                # 設定・定数定義
    ├── 🔧 data_processor.py        # データ処理モジュール
    └── 🖥️ dashboard.py             # メインダッシュボード
```

## ⚙️ 設定とカスタマイズ

### 対象ツールの変更
`src/config.py` でツール一覧を編集：

```python
UPSTREAM_TOOLS = [
    'ChatGPT / Gemini / Claude（会話）',
    'ChatGPT / Gemini / Claude（コーディング）',
    # 新しいツールを追加
]
```

### 表示名の変更
長いツール名を短縮表示：

```python
TOOL_DISPLAY_NAMES = {
    'ChatGPT / Gemini / Claude（会話）': '汎用AI（会話）',
    'ChatGPT / Gemini / Claude（コーディング）': '汎用AI（コーディング）',
}
```

### 評価スケールの調整
頻度・貢献度・時間削減の評価マッピングを変更可能。

## 🛠️ メンテナンス

### データ更新
1. 新しいTSVファイルを `data/` に配置
2. Streamlitキャッシュクリア: `streamlit cache clear`
3. アプリケーション再起動

### パフォーマンス最適化
- 処理済みデータは自動でキャッシュされます
- 大容量データの場合は `data/processed/` を定期的にクリーニング

## 🐛 トラブルシューティング

### よくある問題

**📄 データが表示されない**
```bash
# キャッシュをクリアして再起動
streamlit cache clear
streamlit run src/dashboard.py
```

**🔤 日本語フォントエラー**
```python
# dashboard.py の create_wordcloud 関数でフォントパス調整
# Mac: '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc'
# Windows: 'C:/Windows/Fonts/msgothic.ttc' 
```

**📊 TSVファイル読み込みエラー**
- エンコーディングがUTF-8であることを確認
- ファイル名が正確に `AI活用アンケートデータ.tsv` であることを確認
- 列名が期待される形式と一致していることを確認

## 📈 今後の拡張予定

- 🔄 リアルタイムデータ更新機能
- 📊 より詳細な統計分析（相関分析・回帰分析）
- 📁 エクスポート機能（PDF・Excel出力）
- 🚨 異常値検出とアラート機能
- 📱 モバイル対応の改善

## 🤝 貢献

プロジェクトへの貢献を歓迎します！

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 📞 サポート

- 🐛 バグ報告: [Issues](https://github.com/dev-omotenashi/ai-usage-survey/issues)
- 💡 機能要望: [Discussions](https://github.com/dev-omotenashi/ai-usage-survey/discussions)
- 📖 詳細仕様: [CLAUDE.md](CLAUDE.md)

---

**観光ビッグデータ事業部** | dev-omotenashi組織