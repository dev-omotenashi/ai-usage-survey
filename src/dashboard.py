"""
AI活用アンケート分析ダッシュボード
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime
import os

from data_processor import AIUsageSurveyProcessor
from config import *

def get_display_name(tool_name):
    """ツール名の表示用ラベルを取得"""
    return TOOL_DISPLAY_NAMES.get(tool_name, tool_name)


st.set_page_config(
    page_title="AI活用状況ダッシュボード",
    page_icon="🤖",
    layout="wide"
)


@st.cache_data
def load_and_process_data():
    """データの読み込みと処理"""
    processor = AIUsageSurveyProcessor()
    processor.process_all()
    return processor.df, processor.processed_data


def create_frequency_heatmap(data, title, process_type):
    """利用頻度のヒートマップを作成"""
    tools = UPSTREAM_TOOLS if process_type == 'upstream' else DEVELOPMENT_TOOLS
    
    # 工程に応じて対象チームを設定
    if process_type == 'upstream':
        target_team = 'ディレクターチーム'
        display_label = '上流工程（ディレクターチーム）'
    else:
        target_team = 'エンジニアリングチーム'
        display_label = '開発工程（エンジニアリングチーム）'
    
    # データを整形
    row_data = []
    for tool in tools:
        if tool in data:
            tool_data = data[tool]
            team_data = tool_data[tool_data['あなたが所属するチームはどちらですか？'] == target_team]
            if not team_data.empty:
                # 3列目の列名を取得して平均を計算
                score_column = team_data.columns[2]
                avg_freq = team_data[score_column].mean()
                row_data.append(avg_freq if pd.notna(avg_freq) else 0)
            else:
                row_data.append(0)
        else:
            row_data.append(0)
    
    matrix_data = [row_data]
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix_data,
        x=[get_display_name(t) for t in tools],
        y=[display_label],
        colorscale='Blues',
        text=[[f'{val:.1f}' for val in row] for row in matrix_data],
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title="平均頻度"),
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="AIツール",
        yaxis_title="",
        height=200,
        xaxis={'tickangle': -45}
    )
    
    return fig


def create_time_series_chart(data, title, metric_type, process_type):
    """時系列推移グラフを作成"""
    fig = go.Figure()
    
    # 工程に応じて対象チームを設定
    if process_type == 'upstream':
        target_team = 'ディレクターチーム'
        process_label = '上流工程（ディレクターチーム）'
    else:
        target_team = 'エンジニアリングチーム'
        process_label = '開発工程（エンジニアリングチーム）'
    
    colors = px.colors.qualitative.Set2
    color_idx = 0
    
    for tool, tool_data in data.items():
        if len(tool_data) > 0:
            # 対象チームのデータのみフィルタリング
            team_data = tool_data[tool_data['あなたが所属するチームはどちらですか？'] == target_team]
            if len(team_data) > 0:
                fig.add_trace(go.Scatter(
                    x=team_data['年月'],
                    y=team_data.iloc[:, 2],
                    mode='lines+markers',
                    name=get_display_name(tool),
                    line=dict(color=colors[color_idx % len(colors)]),
                    marker=dict(size=8)
                ))
                color_idx += 1
    
    fig.update_layout(
        title=title,
        xaxis_title="年月",
        yaxis_title="平均スコア",
        height=600,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="rgba(0, 0, 0, 0.2)",
            borderwidth=1,
            font=dict(size=12),
            itemsizing="constant",
            itemwidth=30
        ),
        margin=dict(b=180, r=50, l=80, t=80)
    )
    
    return fig


def create_time_reduction_chart(data, title):
    """時間削減効果の棒グラフを作成"""
    all_data = []
    
    for task, task_data in data.items():
        if len(task_data) > 0:
            avg_reduction = task_data.iloc[:, 2].mean()
            if pd.notna(avg_reduction):
                all_data.append({
                    'タスク': task[:30] + '...' if len(task) > 30 else task,
                    '削減率': avg_reduction
                })
    
    if all_data:
        df = pd.DataFrame(all_data)
        df = df.sort_values('削減率', ascending=True)
        
        fig = go.Figure(go.Bar(
            x=df['削減率'],
            y=df['タスク'],
            orientation='h',
            marker_color=['red' if x < 0 else 'green' for x in df['削減率']]
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="時間削減率 (%)",
            yaxis_title="作業内容",
            height=400,
            margin=dict(l=200)
        )
        
        return fig
    
    return None


def get_time_reduction_examples(raw_df, process_type):
    """時間削減効果の具体的な事例を取得"""
    if process_type == 'upstream':
        target_team = 'ディレクターチーム'
        # 上流工程の具体的事例列
        example_col = '上流工程でAIツールを活用したことで、特に効果を実感した作業や具体的なエピソードがあれば教えてください。'
    else:
        target_team = 'エンジニアリングチーム'
        # 開発工程の具体的事例列
        example_col = '開発工程において、AIツールを活用することで、おおよそどの程度の時間や労力が削減できたと感じますか？（可能な範囲で、具体的な作業とともにご記入ください）'
    
    if example_col not in raw_df.columns:
        return []
    
    # 対象チームのデータでフィルタリング
    team_data = raw_df[raw_df['あなたが所属するチームはどちらですか？'] == target_team]
    
    # 具体的な事例を取得（空でない回答のみ）
    examples = team_data[example_col].dropna()
    examples = examples[examples.str.strip() != '']
    
    return examples.tolist()


def create_time_reduction_trend_chart(data, title, process_type):
    """時間削減効果の推移グラフを作成"""
    fig = go.Figure()
    
    # 工程に応じて対象チームを設定
    if process_type == 'upstream':
        target_team = 'ディレクターチーム'
    else:
        target_team = 'エンジニアリングチーム'
    
    colors = px.colors.qualitative.Set2
    color_idx = 0
    
    for task, task_data in data.items():
        if len(task_data) > 0:
            # 対象チームのデータのみフィルタリング
            team_data = task_data[task_data['あなたが所属するチームはどちらですか？'] == target_team]
            if len(team_data) > 0:
                # タスク名を短縮
                short_task_name = task[:20] + '...' if len(task) > 20 else task
                
                fig.add_trace(go.Scatter(
                    x=team_data['年月'],
                    y=team_data.iloc[:, 2],
                    mode='lines+markers',
                    name=short_task_name,
                    line=dict(color=colors[color_idx % len(colors)]),
                    marker=dict(size=8)
                ))
                color_idx += 1
    
    fig.update_layout(
        title=title,
        xaxis_title="年月",
        yaxis_title="時間削減率 (%)",
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="rgba(0, 0, 0, 0.2)",
            borderwidth=1,
            font=dict(size=12),
            itemsizing="constant",
            itemwidth=30
        ),
        margin=dict(b=180, r=50, l=80, t=80)
    )
    
    return fig


def calculate_time_reduction_metrics(data, process_type):
    """工程別の時間削減効果指標を計算"""
    if process_type == 'upstream':
        target_team = 'ディレクターチーム'
    else:
        target_team = 'エンジニアリングチーム'
    
    # 各作業の月別削減率を収集
    task_scores = {}
    
    for task, task_data in data.items():
        team_data = task_data[task_data['あなたが所属するチームはどちらですか？'] == target_team]
        
        if not team_data.empty:
            # 月別の平均削減率を計算（3列目のデータを使用）
            score_column = team_data.columns[2]  # 3列目の列名を取得
            monthly_scores = team_data.groupby('年月')[score_column].mean().to_dict()
            task_scores[task] = monthly_scores
    
    # 1. 最高削減効果作業（全期間の平均）
    overall_avg = {}
    for task, scores in task_scores.items():
        if scores:
            valid_scores = [v for v in scores.values() if pd.notna(v)]
            if valid_scores:
                overall_avg[task] = sum(valid_scores) / len(valid_scores)
    
    best_task = max(overall_avg, key=overall_avg.get) if overall_avg else None
    best_score = overall_avg.get(best_task, 0) if best_task else 0
    
    # 2. 5月から7月で最も改善した作業
    # 3. 平均削減効果
    improvements = {}
    all_scores = []
    
    for task, scores in task_scores.items():
        if '2025年5月' in scores and '2025年7月' in scores:
            may_score = scores['2025年5月']
            jul_score = scores['2025年7月']
            if pd.notna(may_score) and pd.notna(jul_score):
                improvement = jul_score - may_score
                improvements[task] = {
                    'improvement': improvement,
                    'may_score': may_score,
                    'jul_score': jul_score
                }
        
        # 全スコアを収集（平均計算用）
        for score in scores.values():
            if pd.notna(score):
                all_scores.append(score)
    
    # 最高改善作業
    improved_task = None
    max_improvement = 0
    for task, improvement_data in improvements.items():
        if improvement_data['improvement'] > max_improvement:
            max_improvement = improvement_data['improvement']
            improved_task = task
    
    # 平均削減効果
    avg_reduction = sum(all_scores) / len(all_scores) if all_scores else 0
    
    # 4. 効果的作業割合（削減効果 > 0の作業数）
    effective_tasks = sum(1 for avg in overall_avg.values() if avg > 0)
    total_tasks = len(overall_avg)
    effective_ratio = (effective_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    return {
        'best_task': best_task,
        'best_score': best_score,
        'improved_task': improved_task,
        'improvement': max_improvement,
        'avg_reduction': avg_reduction,
        'effective_ratio': effective_ratio,
        'effective_count': effective_tasks,
        'total_count': total_tasks
    }


def calculate_tool_metrics(frequency_data, contribution_data, process_type):
    """工程別のAIツール指標を計算"""
    if process_type == 'upstream':
        target_team = 'ディレクターチーム'
        tools = UPSTREAM_TOOLS
    else:
        target_team = 'エンジニアリングチーム'
        tools = DEVELOPMENT_TOOLS
    
    # 利用頻度データの処理
    freq_tool_scores = {}
    for tool in tools:
        if tool in frequency_data:
            tool_data = frequency_data[tool]
            team_data = tool_data[tool_data['あなたが所属するチームはどちらですか？'] == target_team]
            
            if not team_data.empty:
                score_column = team_data.columns[2]
                monthly_scores = team_data.groupby('年月')[score_column].mean().to_dict()
                freq_tool_scores[tool] = monthly_scores
    
    # 貢献度データの処理
    contrib_tool_scores = {}
    for tool in tools:
        if tool in contribution_data:
            tool_data = contribution_data[tool]
            team_data = tool_data[tool_data['あなたが所属するチームはどちらですか？'] == target_team]
            
            if not team_data.empty:
                score_column = team_data.columns[2]
                monthly_scores = team_data.groupby('年月')[score_column].mean().to_dict()
                contrib_tool_scores[tool] = monthly_scores
    
    # 1. 最高利用ツール（利用頻度平均が最高）
    freq_overall_avg = {}
    for tool, scores in freq_tool_scores.items():
        if scores:
            valid_scores = [v for v in scores.values() if pd.notna(v)]
            if valid_scores:
                freq_overall_avg[tool] = sum(valid_scores) / len(valid_scores)
    
    most_used_tool = max(freq_overall_avg, key=freq_overall_avg.get) if freq_overall_avg else None
    most_used_score = freq_overall_avg.get(most_used_tool, 0) if most_used_tool else 0
    
    # 2. 最高貢献ツール（貢献度平均が最高）
    contrib_overall_avg = {}
    for tool, scores in contrib_tool_scores.items():
        if scores:
            valid_scores = [v for v in scores.values() if pd.notna(v)]
            if valid_scores:
                contrib_overall_avg[tool] = sum(valid_scores) / len(valid_scores)
    
    best_contrib_tool = max(contrib_overall_avg, key=contrib_overall_avg.get) if contrib_overall_avg else None
    best_contrib_score = contrib_overall_avg.get(best_contrib_tool, 0) if best_contrib_tool else 0
    
    # 3. 総合評価最高（利用頻度×貢献度が最高）
    combined_scores = {}
    for tool in tools:
        freq_avg = freq_overall_avg.get(tool, 0)
        contrib_avg = contrib_overall_avg.get(tool, 0)
        if freq_avg > 0 and contrib_avg > 0:
            combined_scores[tool] = freq_avg * contrib_avg
    
    best_combined_tool = max(combined_scores, key=combined_scores.get) if combined_scores else None
    best_combined_score = combined_scores.get(best_combined_tool, 0) if best_combined_tool else 0
    
    # 4. 最高改善ツール（5月→7月で利用頻度が最も向上）
    improvements = {}
    for tool, scores in freq_tool_scores.items():
        if '2025年5月' in scores and '2025年7月' in scores:
            may_score = scores['2025年5月']
            jul_score = scores['2025年7月']
            if pd.notna(may_score) and pd.notna(jul_score) and may_score > 0:
                improvement = jul_score - may_score
                improvements[tool] = improvement
    
    improved_tool = max(improvements, key=improvements.get) if improvements else None
    improvement_value = improvements.get(improved_tool, 0) if improved_tool else 0
    
    return {
        'most_used_tool': most_used_tool,
        'most_used_score': most_used_score,
        'best_contrib_tool': best_contrib_tool,
        'best_contrib_score': best_contrib_score,
        'best_combined_tool': best_combined_tool,
        'best_combined_score': best_combined_score,
        'improved_tool': improved_tool,
        'improvement_value': improvement_value
    }


def create_frequency_contribution_cross_table(frequency_data, contribution_data, tool_name, process_type):
    """利用頻度×貢献度のクロス集計表を作成"""
    if process_type == 'upstream':
        target_team = 'ディレクターチーム'
    else:
        target_team = 'エンジニアリングチーム'
    
    # 生データを取得
    raw_df = AIUsageSurveyProcessor().load_data()
    team_data = raw_df[raw_df['あなたが所属するチームはどちらですか？'] == target_team]
    
    # 列名を構築
    if process_type == 'upstream':
        freq_col = f'先月で、上流工程の作業において、以下のAIツールをどのくらいの頻度で利用しましたか？ [{tool_name}]'
        contrib_col = f'上流工程の作業において、それぞれのAIツールは担当された作業の生産性向上にどの程度貢献したと感じますか？ [{tool_name}]'
    else:
        freq_col = f'先月、開発工程の作業において、以下のAIツールをどのくらいの頻度で利用しましたか？ [{tool_name}]'
        contrib_col = f'開発工程の作業において、それぞれのAIツールは担当された作業の生産性向上にどの程度貢献したと感じますか？ [{tool_name}]'
    
    if freq_col not in team_data.columns or contrib_col not in team_data.columns:
        return None
    
    # データをフィルタリング（空値を除外）
    valid_data = team_data[[freq_col, contrib_col]].dropna()
    valid_data = valid_data[(valid_data[freq_col] != '') & (valid_data[contrib_col] != '')]
    
    if len(valid_data) == 0:
        return None
    
    # クロス集計表を作成
    cross_table = pd.crosstab(
        valid_data[freq_col], 
        valid_data[contrib_col], 
        margins=True, 
        margins_name="合計"
    )
    
    # 順序を定義
    freq_order = ['利用したことがない', 'ほとんど利用しない', '月に数回', '週に数回', '毎日']
    contrib_order = ['1:全く貢献しなかった', '2:あまり貢献しなかった', '3:どちらともいえない', '4:貢献した', '5:非常に貢献した', '利用していない/判断できない']
    
    # 存在する項目のみでフィルタリング
    existing_freq = [f for f in freq_order if f in cross_table.index]
    existing_contrib = [c for c in contrib_order if c in cross_table.columns]
    
    # 順序に従って並び替え
    cross_table = cross_table.reindex(index=existing_freq + ['合計'], columns=existing_contrib + ['合計'], fill_value=0)
    
    return cross_table


def create_frequency_contribution_heatmap(frequency_data, contribution_data, title, process_type):
    """利用頻度×貢献度の組み合わせヒートマップを作成"""
    tools = UPSTREAM_TOOLS if process_type == 'upstream' else DEVELOPMENT_TOOLS
    
    # 工程に応じて対象チームを設定
    if process_type == 'upstream':
        target_team = 'ディレクターチーム'
        display_label = '上流工程（ディレクターチーム）'
    else:
        target_team = 'エンジニアリングチーム'
        display_label = '開発工程（エンジニアリングチーム）'
    
    # 5月から7月のデータを結合
    target_months = ['2025年5月', '2025年6月', '2025年7月']
    
    combined_scores = []
    tool_labels = []
    
    for tool in tools:
        # 利用頻度の平均を算出
        freq_scores = []
        if tool in frequency_data:
            freq_tool_data = frequency_data[tool]
            freq_team_data = freq_tool_data[freq_tool_data['あなたが所属するチームはどちらですか？'] == target_team]
            
            if not freq_team_data.empty:
                score_column = freq_team_data.columns[2]
                for month in target_months:
                    month_data = freq_team_data[freq_team_data['年月'] == month]
                    if not month_data.empty:
                        # 空文字やNaNを除外して数値のみを収集
                        valid_scores = month_data[score_column].dropna()
                        valid_scores = valid_scores[valid_scores != '']
                        if len(valid_scores) > 0:
                            freq_scores.extend(valid_scores.tolist())
        
        # 貢献度の平均を算出
        contrib_scores = []
        if tool in contribution_data:
            contrib_tool_data = contribution_data[tool]
            contrib_team_data = contrib_tool_data[contrib_tool_data['あなたが所属するチームはどちらですか？'] == target_team]
            
            if not contrib_team_data.empty:
                score_column = contrib_team_data.columns[2]
                for month in target_months:
                    month_data = contrib_team_data[contrib_team_data['年月'] == month]
                    if not month_data.empty:
                        # 空文字やNaNを除外して数値のみを収集
                        valid_scores = month_data[score_column].dropna()
                        valid_scores = valid_scores[valid_scores != '']
                        if len(valid_scores) > 0:
                            contrib_scores.extend(valid_scores.tolist())
        
        # 平均を算出し、掛け算
        freq_avg = sum(freq_scores) / len(freq_scores) if freq_scores else 0
        contrib_avg = sum(contrib_scores) / len(contrib_scores) if contrib_scores else 0
        combined_score = freq_avg * contrib_avg
        
        combined_scores.append(combined_score)
        tool_labels.append(get_display_name(tool))
    
    # デバッグ情報をStreamlitに表示
    if len(combined_scores) == 0 or all(score == 0 for score in combined_scores):
        st.warning(f"⚠️ {process_type}工程のヒートマップデータが不足しています。利用頻度または貢献度のデータを確認してください。")
    
    # ヒートマップ用のデータを整形
    matrix_data = [combined_scores]
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix_data,
        x=tool_labels,
        y=[display_label],
        colorscale='Blues',
        text=[[f'{val:.1f}' for val in row] for row in matrix_data],
        texttemplate='%{text}',
        textfont={"size": 12},
        colorbar=dict(title="利用頻度×貢献度"),
        hovertemplate='%{x}<br>スコア: %{z:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="AIツール",
        yaxis_title="",
        height=300,
        xaxis={'tickangle': -45},
        margin=dict(l=50, r=50, t=80, b=100)
    )
    
    return fig


def create_time_reduction_metrics_cards(metrics, process_label):
    """時間削減効果の指標カードを作成"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if metrics['best_task']:
            task_name = metrics['best_task'][:15] + '...' if len(metrics['best_task']) > 15 else metrics['best_task']
            st.metric(
                label=f"🏆 {process_label}最高削減効果",
                value=task_name,
                delta=f"{metrics['best_score']:.1f}%削減"
            )
        else:
            st.metric(
                label=f"🏆 {process_label}最高削減効果",
                value="データなし"
            )
    
    with col2:
        if metrics['improved_task']:
            task_name = metrics['improved_task'][:15] + '...' if len(metrics['improved_task']) > 15 else metrics['improved_task']
            st.metric(
                label=f"📈 5月→7月 最高改善",
                value=task_name,
                delta=f"+{metrics['improvement']:.1f}pt改善"
            )
        else:
            st.metric(
                label=f"📈 5月→7月 最高改善",
                value="データなし"
            )
    
    with col3:
        st.metric(
            label=f"📊 {process_label}平均削減効果",
            value=f"{metrics['avg_reduction']:.1f}%",
            delta="全作業平均"
        )
    
    with col4:
        st.metric(
            label=f"✅ 効果的作業割合",
            value=f"{metrics['effective_ratio']:.0f}%",
            delta=f"{metrics['effective_count']}/{metrics['total_count']}作業"
        )


def create_metrics_cards(metrics, process_label):
    """指標カードを作成"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if metrics['most_used_tool']:
            tool_name = get_display_name(metrics['most_used_tool'])
            st.metric(
                label=f"🏆 {process_label}最高利用ツール",
                value=tool_name,
                delta=f"平均{metrics['most_used_score']:.1f}点"
            )
        else:
            st.metric(
                label=f"🏆 {process_label}最高利用ツール",
                value="データなし"
            )
    
    with col2:
        if metrics['best_contrib_tool']:
            tool_name = get_display_name(metrics['best_contrib_tool'])
            st.metric(
                label=f"⭐ {process_label}最高貢献ツール",
                value=tool_name,
                delta=f"平均{metrics['best_contrib_score']:.1f}点"
            )
        else:
            st.metric(
                label=f"⭐ {process_label}最高貢献ツール",
                value="データなし"
            )
    
    with col3:
        if metrics['best_combined_tool']:
            tool_name = get_display_name(metrics['best_combined_tool'])
            st.metric(
                label=f"🎯 {process_label}総合評価最高",
                value=tool_name,
                delta=f"総合{metrics['best_combined_score']:.1f}点"
            )
        else:
            st.metric(
                label=f"🎯 {process_label}総合評価最高",
                value="データなし"
            )
    
    with col4:
        if metrics['improved_tool']:
            tool_name = get_display_name(metrics['improved_tool'])
            st.metric(
                label=f"📈 5月→7月 最高改善",
                value=tool_name,
                delta=f"+{metrics['improvement_value']:.1f}pt"
            )
        else:
            st.metric(
                label=f"📈 5月→7月 最高改善",
                value="データなし"
            )


def create_wordcloud(text_list):
    """ワードクラウドを作成"""
    if not text_list:
        return None
    
    text = ' '.join([str(t) for t in text_list if pd.notna(t)])
    if not text:
        return None
    
    # 日本語フォントの設定（環境に応じて調整が必要）
    try:
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            font_path='/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc',
            prefer_horizontal=0.7
        ).generate(text)
    except:
        # フォントが見つからない場合は英語のみ
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            prefer_horizontal=0.7
        ).generate(text)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    
    return fig


def main():
    st.title("🤖 AI活用状況分析ダッシュボード")
    st.markdown("### 3ヶ月間のAIツール利用傾向と効果分析")
    
    # データ読み込み
    with st.spinner('データを読み込んでいます...'):
        df, processed_data = load_and_process_data()
    
    # サイドバー - 調査情報パネル
    st.sidebar.header("📊 調査情報")
    
    # 基本情報
    available_months = sorted(df['年月'].unique())
    total_responses = len(df)
    eng_responses = len(df[df['あなたが所属するチームはどちらですか？'] == 'エンジニアリングチーム'])
    dir_responses = len(df[df['あなたが所属するチームはどちらですか？'] == 'ディレクターチーム'])
    
    st.sidebar.markdown(f"""
    **調査期間**: {available_months[0]} 〜 {available_months[-1]}
    
    **対象期間**: {len(available_months)}ヶ月間
    
    **総回答数**: {total_responses}件
    - 上流工程: {dir_responses}件
    - 開発工程: {eng_responses}件
    
    **対象組織**: 観光ビッグデータ事業部
    """)
    
    st.sidebar.markdown("---")
    
    # データ更新情報
    st.sidebar.subheader("📈 データ情報")
    st.sidebar.markdown(f"""
    **最新データ**: {available_months[-1]}
    
    **データ範囲**: 
    - 利用頻度（5段階評価）
    - 生産性貢献度（5段階評価）  
    - 時間削減効果（6段階評価）
    - 具体的事例・課題
    """)
    
    st.sidebar.markdown("---")
    
    # ダッシュボード使い方ガイド
    st.sidebar.subheader("🔍 ダッシュボードガイド")
    st.sidebar.markdown("""
    **📊 概要タブ**
    - 調査の背景と目的
    - 対象ツール・作業一覧
    - 基本統計情報
    
    **📈 利用頻度・生産性分析**
    - 工程別の指標カード
    - ツール利用頻度の推移
    - 生産性貢献度の分析
    - ツール別クロス集計
    
    **⏱️ 時間削減効果**
    - 削減効果の指標カード
    - 作業別削減率グラフ
    - 月別推移チャート
    - 具体的な事例紹介
    
    **📝 課題・フィードバック**
    - 課題の集計結果
    - フィードバック分析
    - 改善要望の整理
    """)
    
    st.sidebar.markdown("---")
    
    # データ解釈のヒント
    st.sidebar.subheader("💡 データ解釈のヒント")
    st.sidebar.markdown("""
    **指標カード**
    - 🏆: 最も頻繁に使用
    - ⭐: 最も生産性向上に貢献
    - 🎯: 総合的に最も効果的
    - 📈: 習熟により最も改善
    
    **スコアの意味**
    - 利用頻度: 1〜5点（高い=頻繁に利用）
    - 貢献度: 1〜5点（高い=生産性向上に貢献）
    - 削減率: -10〜100%（高い=時間削減効果大）
    
    **活用のポイント**
    - 高スコアツールの活用拡大
    - 低スコアツールの改善検討
    - 事例から具体的な使い方を学習
    """)
    
    # メインコンテンツ
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 概要", "📈 利用頻度・生産性分析", "⏱️ 時間削減効果", "📝 課題・フィードバック"
    ])
    
    with tab1:
        st.header("概要")
        
        # 調査概要
        st.markdown("""
        <br>
        
        ### 📋 調査概要
        
        本ダッシュボードは、**観光ビッグデータ事業部**でのAI利活用度について毎月実施しているアンケート調査の結果をまとめたものです。
        
        **調査目的**: AIツールの利用状況と生産性への影響を定量的に把握し、効果的な活用方法を検討する
        
        **調査対象**: 
        - **ディレクターチーム**: 上流工程（企画・設計・要件定義等）を担当
        - **エンジニアリングチーム**: 開発工程（実装・テスト・レビュー等）を担当
        
        <br>
        """, unsafe_allow_html=True)
        
        # アンケート項目概要
        st.markdown("""
        ### 📝 アンケート項目概要
        """)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("""
            #### 🔵 上流工程（ディレクターチーム）
            
            **対象ツール:**
            - ChatGPT
            - Gemini  
            - genspark
            - bolt.new
            - Notebook LM
            - Devin Search
            - その他のAIツール
            
            **対象作業:**
            - 企画・提案の骨子検討
            - 提案資料作成
            - 仕様・要件整理（UI含む）
            - 概要設計・システム構成検討
            - プレゼン・説明内容の整理
            - 事務作業
            """)
        
        with col_right:
            st.markdown("""
            #### 🟢 開発工程（エンジニアリングチーム）
            
            **対象ツール:**
            - ChatGPT/Gemini/Claude（会話）
            - ChatGPT/Gemini/Claude（コーディング）
            - Devin (Session/Search/wiki)
            - GitHub Copilot
            - Cursor
            - Claude (ClaudeCode)
            - その他
            
            **対象作業:**
            - 技術的な調査、問題解決のための情報収集
            - 設計作業（検討・整理含む）
            - コーディング作業
            - 単体テスト作業（テストケース作成・実行）
            - レビュー（コードや設計）
            """)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("""
        ### 📊 調査項目
        - **利用頻度**: 各ツールをどのくらいの頻度で利用するか（5段階評価）
        - **生産性貢献度**: 各ツールが作業の生産性向上にどの程度貢献したか（5段階評価）
        - **時間削減効果**: 各作業でAIツール活用により削減できた時間・労力（6段階評価）
        - **具体的事例**: 効果を実感した作業の具体的なエピソード
        - **課題・要望**: AIツール活用上の課題や改善要望
        
        <br>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 回答数サマリー
        st.subheader("📈 回答数サマリー")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("総回答数", len(df))
        
        with col2:
            eng_count = len(df[df['あなたが所属するチームはどちらですか？'] == 'エンジニアリングチーム'])
            st.metric("エンジニアリング", eng_count)
        
        with col3:
            dir_count = len(df[df['あなたが所属するチームはどちらですか？'] == 'ディレクターチーム'])
            st.metric("ディレクター", dir_count)
        
        with col4:
            st.metric("調査期間", f"{len(available_months)}ヶ月")
        
        # 回答数の推移
        st.subheader("月別回答数の推移")
        monthly_counts = df.groupby(['年月', 'あなたが所属するチームはどちらですか？']).size().reset_index(name='回答数')
        
        fig = px.bar(
            monthly_counts,
            x='年月',
            y='回答数',
            color='あなたが所属するチームはどちらですか？',
            title="月別回答数",
            barmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("利用頻度・生産性分析")
        
        # 上流工程のセクション
        with st.container():
            st.markdown("""
            <div style="
                background-color: #f0f8ff;
                padding: 20px;
                border-radius: 10px;
                margin: 30px 0;
                border-left: 5px solid #4682b4;
            ">
            <h3 style="margin-top: 0; color: #4682b4;">上流工程（ディレクターチーム）</h3>
            """, unsafe_allow_html=True)
            
            if 'upstream_frequency' in processed_data:
                # 指標カードを表示
                upstream_metrics = calculate_tool_metrics(
                    processed_data['upstream_frequency'], 
                    processed_data.get('upstream_contribution', {}), 
                    'upstream'
                )
                create_metrics_cards(upstream_metrics, "上流工程")
            
            st.markdown("---")  # 区切り線
            fig = create_frequency_heatmap(
                processed_data['upstream_frequency'],
                "AIツール利用頻度",
                'upstream'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 時系列推移
            st.markdown("### 利用頻度の推移")
            
            # 説明文を追加
            st.markdown("""
            **アンケート質問:** 「先月で、上流工程の作業において、以下のAIツールをどのくらいの頻度で利用しましたか？」
            
            **回答選択肢とスコア:**
            - 毎日 (5点)
            - 週に数回 (4点)
            - 月に数回 (3点)
            - ほとんど利用しない (2点)
            - 利用したことがない (1点)
            
            **対象AIツール:** ChatGPT, Gemini, genspark, bolt.new, Notebook LM, Devin Search, その他のAIツール
            
            **計算方法:** 各月のディレクターチームの回答者の平均スコアを表示。高いほど頻繁に利用されていることを示す。
            """)
            
            fig = create_time_series_chart(
                processed_data['upstream_frequency'],
                "利用頻度の推移",
                'frequency',
                'upstream'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 貢献度の推移
            st.markdown("### 生産性への貢献度の推移")
            
            # 説明文を追加
            st.markdown("""
            **アンケート質問:** 「上流工程の作業において、それぞれのAIツールは担当された作業の生産性向上にどの程度貢献したと感じますか？」
            
            **回答選択肢とスコア:**
            - 5:非常に貢献した (5点)
            - 4:貢献した (4点)
            - 3:どちらともいえない (3点)
            - 2:あまり貢献しなかった (2点)
            - 1:全く貢献しなかった (1点)
            - 利用していない/判断できない (0点)
            
            **対象AIツール:** ChatGPT, Gemini, genspark, bolt.new, Notebook LM, Devin Search, その他のAIツール
            
            **計算方法:** 各月のディレクターチームの回答者の平均スコアを表示。高いほど生産性向上に貢献していると感じられていることを示す。
            """)
            
            if 'upstream_contribution' in processed_data:
                fig = create_time_series_chart(
                    processed_data['upstream_contribution'],
                    "貢献度の推移",
                    'contribution',
                    'upstream'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # 利用頻度×貢献度の組み合わせ
            st.markdown("### 利用頻度×生産性貢献度")
            
            # 説明文を追加
            st.markdown("""
            **計算方法:** 5月から7月の各ツールの利用頻度平均と貢献度平均を掛け合わせたスコア。
            
            **意味:** 高いスコアは「頻繁に使われており、かつ生産性向上に貢献している」ツールであることを示し、実際の業務インパクトが高いツールを特定できます。
            
            **活用方法:** スコアが高いツールは継続利用を推奨、低いツールは使い方の改善や代替手段の検討が推奨されます。
            """)
            
            if 'upstream_frequency' in processed_data and 'upstream_contribution' in processed_data:
                try:
                    fig = create_frequency_contribution_heatmap(
                        processed_data['upstream_frequency'],
                        processed_data['upstream_contribution'],
                        "利用頻度×貢献度組み合わせ",
                        'upstream'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"上流工程のヒートマップ表示エラー: {e}")
            else:
                st.warning("上流工程の利用頻度または貢献度データが見つかりません。")
            
            # ツール別のクロス集計表
            st.markdown("#### ツール別クロス集計表")
            st.markdown("利用頻度と生産性貢献度の詳細な関係を確認できます。")
            
            # ツール選択
            selected_tool = st.selectbox(
                "詳細を確認するツールを選択",
                UPSTREAM_TOOLS,
                key="upstream_tool_select"
            )
            
            if selected_tool:
                cross_table = create_frequency_contribution_cross_table(
                    processed_data['upstream_frequency'],
                    processed_data['upstream_contribution'],
                    selected_tool,
                    'upstream'
                )
                
                if cross_table is not None:
                    st.markdown(f"**{get_display_name(selected_tool)}の利用頻度×生産性貢献度クロス集計**")
                    st.dataframe(cross_table, use_container_width=True)
                    
                    # 合計行・列を除いたヒートマップ
                    heatmap_data = cross_table.iloc[:-1, :-1]  # 合計行・列を除外
                    if not heatmap_data.empty:
                        fig_cross = go.Figure(data=go.Heatmap(
                            z=heatmap_data.values,
                            x=heatmap_data.columns,
                            y=heatmap_data.index,
                            colorscale='Blues',
                            text=heatmap_data.values,
                            texttemplate='%{text}',
                            textfont={"size": 12},
                            colorbar=dict(title="回答数")
                        ))
                        
                        fig_cross.update_layout(
                            title=f"{get_display_name(selected_tool)} 利用頻度×貢献度",
                            xaxis_title="生産性貢献度",
                            yaxis_title="利用頻度",
                            height=400,
                            xaxis={'tickangle': -45}
                        )
                        
                        st.plotly_chart(fig_cross, use_container_width=True)
                else:
                    st.info(f"{get_display_name(selected_tool)}のデータが不足しています。")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # 開発工程のセクション
        with st.container():
            st.markdown("""
            <div style="
                background-color: #f0fff0;
                padding: 20px;
                border-radius: 10px;
                margin: 30px 0;
                border-left: 5px solid #32cd32;
            ">
            <h3 style="margin-top: 0; color: #32cd32;">開発工程（エンジニアリングチーム）</h3>
            """, unsafe_allow_html=True)
            if 'development_frequency' in processed_data:
                # 指標カードを表示
                development_metrics = calculate_tool_metrics(
                    processed_data['development_frequency'], 
                    processed_data.get('development_contribution', {}), 
                    'development'
                )
                create_metrics_cards(development_metrics, "開発工程")
            
                st.markdown("---")  # 区切り線
                fig = create_frequency_heatmap(
                    processed_data['development_frequency'],
                    "AIツール利用頻度",
                    'development'
                )
                st.plotly_chart(fig, use_container_width=True)
            
                # 時系列推移
                st.markdown("### 利用頻度の推移")
                
                # 説明文を追加
                st.markdown("""
                **アンケート質問:** 「先月、開発工程の作業において、以下のAIツールをどのくらいの頻度で利用しましたか？」
                
                **回答選択肢とスコア:**
                - 毎日 (5点)
                - 週に数回 (4点)
                - 月に数回 (3点)
                - ほとんど利用しない (2点)
                - 利用したことがない (1点)
                
                **対象AIツール:** ChatGPT/Gemini/Claude（会話）, ChatGPT/Gemini/Claude（コーディング）, Devin, GitHub Copilot, Cursor, Claude(ClaudeCode), その他
                
                **計算方法:** 各月のエンジニアリングチームの回答者の平均スコアを表示。高いほど頻繁に利用されていることを示す。
                """)
                
                fig = create_time_series_chart(
                    processed_data['development_frequency'],
                    "利用頻度の推移",
                    'frequency',
                    'development'
                )
                st.plotly_chart(fig, use_container_width=True)
            
                # 貢献度の推移
                st.markdown("### 生産性への貢献度の推移")
                
                # 説明文を追加
                st.markdown("""
                **アンケート質問:** 「開発工程の作業において、それぞれのAIツールは担当された作業の生産性向上にどの程度貢献したと感じますか？」
                
                **回答選択肢とスコア:**
                - 5:非常に貢献した (5点)
                - 4:貢献した (4点)
                - 3:どちらともいえない (3点)
                - 2:あまり貢献しなかった (2点)
                - 1:全く貢献しなかった (1点)
                - 利用していない/判断できない (0点)
                
                **対象AIツール:** ChatGPT/Gemini/Claude（会話）, ChatGPT/Gemini/Claude（コーディング）, Devin, GitHub Copilot, Cursor, Claude(ClaudeCode), その他
                
                **計算方法:** 各月のエンジニアリングチームの回答者の平均スコアを表示。高いほど生産性向上に貢献していると感じられていることを示す。
                """)
                
                if 'development_contribution' in processed_data:
                    fig = create_time_series_chart(
                        processed_data['development_contribution'],
                        "貢献度の推移",
                        'contribution',
                        'development'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
                # 利用頻度×貢献度の組み合わせ
                st.markdown("### 利用頻度×生産性貢献度")
                
                # 説明文を追加
                st.markdown("""
                **計算方法:** 5月から7月の各ツールの利用頻度平均と貢献度平均を掛け合わせたスコア。
                
                **意味:** 高いスコアは「頻繁に使われており、かつ生産性向上に貢献している」ツールであることを示し、実際の業務インパクトが高いツールを特定できます。
                
                **活用方法:** スコアが高いツールは継続利用を推奨、低いツールは使い方の改善や代替手段の検討が推奨されます。
                """)
                
                if 'development_frequency' in processed_data and 'development_contribution' in processed_data:
                    try:
                        fig = create_frequency_contribution_heatmap(
                            processed_data['development_frequency'],
                            processed_data['development_contribution'],
                            "利用頻度×貢献度組み合わせ",
                            'development'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"開発工程のヒートマップ表示エラー: {e}")
                else:
                    st.warning("開発工程の利用頻度または貢献度データが見つかりません。")
                
                # ツール別のクロス集計表
                st.markdown("#### ツール別クロス集計表")
                st.markdown("利用頻度と生産性貢献度の詳細な関係を確認できます。")
                
                # ツール選択
                selected_dev_tool = st.selectbox(
                    "詳細を確認するツールを選択",
                    DEVELOPMENT_TOOLS,
                    key="development_tool_select"
                )
                
                if selected_dev_tool:
                    cross_table = create_frequency_contribution_cross_table(
                        processed_data['development_frequency'],
                        processed_data['development_contribution'],
                        selected_dev_tool,
                        'development'
                    )
                    
                    if cross_table is not None:
                        st.markdown(f"**{get_display_name(selected_dev_tool)}の利用頻度×生産性貢献度クロス集計**")
                        st.dataframe(cross_table, use_container_width=True)
                        
                        # 合計行・列を除いたヒートマップ
                        heatmap_data = cross_table.iloc[:-1, :-1]  # 合計行・列を除外
                        if not heatmap_data.empty:
                            fig_cross = go.Figure(data=go.Heatmap(
                                z=heatmap_data.values,
                                x=heatmap_data.columns,
                                y=heatmap_data.index,
                                colorscale='Blues',
                                text=heatmap_data.values,
                                texttemplate='%{text}',
                                textfont={"size": 12},
                                colorbar=dict(title="回答数")
                            ))
                            
                            fig_cross.update_layout(
                                title=f"{get_display_name(selected_dev_tool)} 利用頻度×貢献度",
                                xaxis_title="生産性貢献度",
                                yaxis_title="利用頻度",
                                height=400,
                                xaxis={'tickangle': -45}
                            )
                            
                            st.plotly_chart(fig_cross, use_container_width=True)
                    else:
                        st.info(f"{get_display_name(selected_dev_tool)}のデータが不足しています。")
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    with tab3:
        st.header("時間・労力削減効果")
        
        # 上流工程のタイトル
        st.markdown("""
        <div style="
            background-color: #e6f3ff;
            padding: 15px 20px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 5px solid #4682b4;
        ">
        <h3 style="margin: 0; color: #4682b4;">上流工程での削減効果</h3>
        </div>
        """, unsafe_allow_html=True)
        if 'upstream_time_reduction' in processed_data:
            # 指標カードを表示
            upstream_time_metrics = calculate_time_reduction_metrics(processed_data['upstream_time_reduction'], 'upstream')
            create_time_reduction_metrics_cards(upstream_time_metrics, "上流工程")
            
            st.markdown("---")  # 区切り線
            
            # 平均削減率（棒グラフ）
            fig = create_time_reduction_chart(
                processed_data['upstream_time_reduction'],
                "作業別時間削減率（上流工程・平均値）"
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # 推移グラフ
            fig_trend = create_time_reduction_trend_chart(
                processed_data['upstream_time_reduction'],
                "時間削減効果の推移（上流工程・5月〜7月）",
                'upstream'
            )
            if fig_trend:
                st.plotly_chart(fig_trend, use_container_width=True)
            
            # 具体的な事例
            st.markdown("### 具体的な削減効果事例")
            examples = get_time_reduction_examples(df, 'upstream')
            if examples:
                st.markdown("**上流工程でAIツールを活用して効果を実感した具体的なエピソード:**")
                
                for i, example in enumerate(examples[:5], 1):  # 最大5件表示
                    # 文章を整形（改行を正規化し、長すぎる場合は要約）
                    cleaned_example = example.replace('\n', ' ').replace('\r', ' ').strip()
                    
                    # 長すぎる場合は最初の100文字 + プレビュー
                    if len(cleaned_example) > 100:
                        preview = cleaned_example[:100] + "..."
                        full_text = cleaned_example
                    else:
                        preview = cleaned_example
                        full_text = cleaned_example
                    
                    # アコーディオン形式で表示
                    with st.expander(f"事例 {i}: {preview}", expanded=False):
                        st.markdown(f"""
                        <div style="
                            background-color: #f8f9fa;
                            padding: 15px;
                            border-radius: 8px;
                            border-left: 4px solid #4682b4;
                            margin: 10px 0;
                        ">
                        {full_text}
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("具体的な事例が記載されていません。")
        
        # 開発工程のタイトル
        st.markdown("""
        <div style="
            background-color: #f0fff0;
            padding: 15px 20px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 5px solid #32cd32;
        ">
        <h3 style="margin: 0; color: #32cd32;">開発工程での削減効果</h3>
        </div>
        """, unsafe_allow_html=True)
        if 'development_time_reduction' in processed_data:
            # 指標カードを表示
            development_time_metrics = calculate_time_reduction_metrics(processed_data['development_time_reduction'], 'development')
            create_time_reduction_metrics_cards(development_time_metrics, "開発工程")
            
            st.markdown("---")  # 区切り線
            
            # 平均削減率（棒グラフ）
            fig = create_time_reduction_chart(
                processed_data['development_time_reduction'],
                "作業別時間削減率（開発工程・平均値）"
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # 推移グラフ
            fig_trend = create_time_reduction_trend_chart(
                processed_data['development_time_reduction'],
                "時間削減効果の推移（開発工程・5月〜7月）",
                'development'
            )
            if fig_trend:
                st.plotly_chart(fig_trend, use_container_width=True)
            
            # 具体的な事例
            st.markdown("### 具体的な削減効果事例")
            examples = get_time_reduction_examples(df, 'development')
            if examples:
                st.markdown("**開発工程でAIツールを活用した具体的な作業内容と削減効果:**")
                
                for i, example in enumerate(examples[:5], 1):  # 最大5件表示
                    # 文章を整形（改行を正規化し、長すぎる場合は要約）
                    cleaned_example = example.replace('\n', ' ').replace('\r', ' ').strip()
                    
                    # 長すぎる場合は最初の100文字 + プレビュー
                    if len(cleaned_example) > 100:
                        preview = cleaned_example[:100] + "..."
                        full_text = cleaned_example
                    else:
                        preview = cleaned_example
                        full_text = cleaned_example
                    
                    # アコーディオン形式で表示
                    with st.expander(f"事例 {i}: {preview}", expanded=False):
                        st.markdown(f"""
                        <div style="
                            background-color: #f0fff0;
                            padding: 15px;
                            border-radius: 8px;
                            border-left: 4px solid #32cd32;
                            margin: 10px 0;
                        ">
                        {full_text}
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("具体的な事例が記載されていません。")
    
    with tab4:
        st.header("課題とフィードバック")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("上流工程での課題")
            if 'upstream_challenges' in processed_data:
                challenges = processed_data['upstream_challenges']
                if len(challenges) > 0:
                    fig = px.bar(
                        x=challenges.values[:10],
                        y=challenges.index[:10],
                        orientation='h',
                        title="主な課題（上位10件）"
                    )
                    fig.update_layout(
                        xaxis_title="回答数",
                        yaxis_title="課題",
                        height=400,
                        margin=dict(l=300)
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("開発工程での課題")
            if 'development_challenges' in processed_data:
                challenges = processed_data['development_challenges']
                if len(challenges) > 0:
                    fig = px.bar(
                        x=challenges.values[:10],
                        y=challenges.index[:10],
                        orientation='h',
                        title="主な課題（上位10件）"
                    )
                    fig.update_layout(
                        xaxis_title="回答数",
                        yaxis_title="課題",
                        height=400,
                        margin=dict(l=300)
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # フィードバックのワードクラウド
        st.subheader("フィードバック・意見のワードクラウド")
        if 'feedback' in processed_data and processed_data['feedback']:
            wordcloud_fig = create_wordcloud(processed_data['feedback'])
            if wordcloud_fig:
                st.pyplot(wordcloud_fig)
            else:
                st.info("ワードクラウドを生成するための十分なテキストがありません。")
        
        # 具体的なフィードバックの表示
        st.subheader("具体的なフィードバック（抜粋）")
        feedback_col = 'AIを活用した開発プロセス全体に関して、その他何か意見や要望があれば自由にご記入ください。'
        if feedback_col in df.columns:
            feedback_data = df[feedback_col].dropna()
            if len(feedback_data) > 0:
                for i, feedback in enumerate(feedback_data.head(5)):
                    st.text_area(f"フィードバック {i+1}", feedback, height=100, disabled=True)


if __name__ == "__main__":
    main()