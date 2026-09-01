# -*- coding: utf-8 -*-
"""Generate PNG figure: Sample quality overview by question category."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

plt.rcParams['font.family'] = ['Microsoft YaHei', 'SimHei', 'sans-serif']
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['font.size'] = 10
plt.rcParams['axes.unicode_minus'] = False

# -- Color palette --
C_SIMPLE = '#00b894'
C_COMPLEX = '#0984e3'
C_AGG = '#6c5ce7'
C_HIGHLIGHT = '#ffeaa7'
C_HIGHLIGHT_BORDER = '#fdcb6e'
C_BG = '#f8f9fa'
C_WHITE = '#ffffff'
C_TEXT = '#2d3436'
C_TEXT_SEC = '#636e72'
C_CODE_BG = '#2d3436'
C_CODE_TEXT = '#dfe6e9'
C_RED = '#d63031'

# -- Figure setup --
FIG_W, FIG_H = 36, 28
fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor=C_BG)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis('off')


def draw_rounded_box(ax, x, y, w, h, color=C_WHITE, ec='#dfe6e9', lw=1.5, radius=0.3):
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle=f"round,pad=0,rounding_size={radius}",
                         facecolor=color, edgecolor=ec, linewidth=lw, zorder=2)
    ax.add_patch(box)


def draw_text(ax, x, y, text, size=10, color=C_TEXT, ha='left', va='center',
              bold=False):
    kw = dict(fontsize=size, color=color, ha=ha, va=va, fontweight='bold' if bold else 'normal')
    ax.text(x, y, text, **kw)


def draw_header_bar(ax, x, y, w, h, text, color, size=13):
    rect = plt.Rectangle((x, y), w, h, facecolor=color, edgecolor='none', zorder=3)
    ax.add_patch(rect)
    draw_text(ax, x + w/2, y + h/2, text, size=size, color='white', ha='center', bold=True)


def draw_sql_box(ax, x, y, w, h, lines, size=8.5):
    rect = plt.Rectangle((x, y), w, h, facecolor=C_CODE_BG, edgecolor='#555',
                         linewidth=0.8, zorder=3)
    ax.add_patch(rect)
    for i, line in enumerate(lines):
        draw_text(ax, x + 0.2, y + h - 0.25 - i * 0.38, line,
                  size=size, color=C_CODE_TEXT, va='top')


# ===== TITLE =====
draw_text(ax, FIG_W/2, FIG_H - 0.8,
          '评测集样本分类展示 -- 简单问题 / 复杂问题 / 聚合问题',
          size=26, color=C_TEXT, ha='center', bold=True)
draw_text(ax, FIG_W/2, FIG_H - 1.5,
          '数据来源: sample_queries_with_sql_100_new_with_data.json  |  '
          '黄色高亮 = 符合查询条件的数值  |  [OK] = 满足约束',
          size=11, color=C_TEXT_SEC, ha='center')

# ===== DATA =====
categories = [
    {
        'name': '简单问题',
        'label': '[A]',
        'subtitle': '单 JOIN . 单一属性过滤',
        'color': C_SIMPLE,
        'samples': [
            {
                'id': '#21', 'query': '硬度大于200的有哪些',
                'query_en': 'Hardness > 200?',
                'sql_lines': [
                    'SELECT DISTINCT e.data_id',
                    'FROM entity_table e',
                    'JOIN value_table v ON v.data_id = e.data_id',
                    'WHERE v.property_id = 189',
                    '  AND CAST(v.value AS DECIMAL) > 200.0',
                ],
                'tags': ['1 JOIN', '单条件', 'CAST'],
                'result_count': '58', 'source_count': '3',
                'source_info': '钢-硬质合金 / 钢-模具钢-硬度 / 微区IF钢',
                'fields': [
                    ('钢号', 'QT600-3', False),
                    ('[MATCH] 硬度 (HB)', '269.0', True),
                    ('碳 C', '3.76 %', False),
                    ('试验温度', '25 C', False),
                ],
                'data_title': '钢-硬质合金_1184'
            },
            {
                'id': '#52', 'query': '帮我找屈服强度在400到800之间的数据',
                'query_en': 'Yield strength between 400 and 800?',
                'sql_lines': [
                    'SELECT DISTINCT e.data_id',
                    'FROM entity_table e',
                    'JOIN value_table v ON v.data_id = e.data_id',
                    'WHERE v.property_id = 21',
                    '  AND CAST(v.value AS DECIMAL) BETWEEN 400.0 AND 800.0',
                ],
                'tags': ['1 JOIN', 'BETWEEN', 'CAST'],
                'result_count': '55', 'source_count': '3',
                'source_info': '钢-屈服强度-数据表 / 钢-屈服强度1 / 钢-屈服强度3',
                'fields': [
                    ('钢号', '70', False),
                    ('[MATCH] 屈服强度', '743 MPa', True),
                    ('碳 C', '0.75 %', False),
                    ('热处理', '820C淬火+480C回火', False),
                ],
                'data_title': '钢-屈服强度-数据表_1573'
            },
            {
                'id': '#62', 'query': '伸长率刚好为16的数据有哪些',
                'query_en': 'Elongation exactly = 16?',
                'sql_lines': [
                    'SELECT DISTINCT e.data_id',
                    'FROM entity_table e',
                    'JOIN value_table v ON v.data_id = e.data_id',
                    'WHERE v.property_id = 31',
                    '  AND CAST(v.value AS DECIMAL) = 16.0',
                ],
                'tags': ['1 JOIN', '精确等值 =', 'CAST'],
                'result_count': '21', 'source_count': '6',
                'source_info': '钢-模具钢-力学性能 / 钢-伸长率 / 钢-硬质合金 等',
                'fields': [
                    ('牌号', '10Ni3MnCuAl', False),
                    ('[MATCH] 伸长率 (%)', '16', True),
                    ('抗拉强度', '1240 MPa', False),
                    ('Ni', '3.11 %', False),
                ],
                'data_title': '钢-模具钢-硬度_414'
            },
        ]
    },
    {
        'name': '复杂问题',
        'label': '[B]',
        'subtitle': '双 JOIN . 多属性联合约束 . BETWEEN 范围',
        'color': C_COMPLEX,
        'samples': [
            {
                'id': '#1', 'query': '有哪些数据晶粒体积大于50000, 半径也大于15?',
                'query_en': 'Grain volume > 50000 AND radius > 15?',
                'sql_lines': [
                    'SELECT DISTINCT e.data_id',
                    'FROM entity_table e',
                    'JOIN value_table v  ON v.data_id = e.data_id   <- volume',
                    'JOIN value_table v2 ON v2.data_id = e.data_id  <- radius',
                    'WHERE v.property_id = 121  AND CAST(v.value) > 50000.0',
                    '  AND v2.property_id = 122 AND CAST(v2.value) > 15.0',
                ],
                'tags': ['2 JOIN', '双条件', 'CASTx2'],
                'result_count': '20', 'source_count': '1',
                'source_info': '3D晶粒信息汇总 (纯铁3D晶粒)',
                'fields': [
                    ('晶粒编号 / 位置', '13656 / 内部', False),
                    ('[MATCH] 体积', '52925.40', True),
                    ('[MATCH] 半径', '23.30', True),
                    ('表面积 / 面数', '9626.09 / 10', False),
                ],
                'data_title': '3D晶粒信息汇总'
            },
            {
                'id': '#18', 'query': '钴基高温合金中, 哪些Co在40到60之间, W大于2?',
                'query_en': 'Co-based superalloys: Co 40-60 AND W > 2?',
                'sql_lines': [
                    'SELECT DISTINCT e.data_id',
                    'FROM entity_table e',
                    'JOIN value_table v  ON v.data_id = e.data_id   <- Co',
                    'JOIN value_table v2 ON v2.data_id = e.data_id  <- W',
                    'WHERE v.property_id = 61  AND CAST(v.value) BETWEEN 40.0 AND 60.0',
                    '  AND v2.property_id = 108 AND CAST(v2.value) > 2.0',
                ],
                'tags': ['2 JOIN', 'BETWEEN', '双条件', 'CASTx2'],
                'result_count': '65', 'source_count': '4',
                'source_info': '钴基高温合金成分-性能 / 成分-组织 / 钢-比热 / 钢-热扩散率',
                'fields': [
                    ('合金类别', '钴基高温合金 (gamma+gamma\')', False),
                    ('[MATCH] Co 含量', '43.12 %', True),
                    ('[MATCH] W 含量', '2.80 %', True),
                    ('Ni / Cr', '30.25% / 12.25%', False),
                ],
                'data_title': '钴基高温合金成分-性能'
            },
            {
                'id': '#50', 'query': '抗拉强度在500到700之间, 钼含量大于0.1的材料',
                'query_en': 'Tensile 500-700 AND Mo > 0.1?',
                'sql_lines': [
                    'SELECT DISTINCT e.data_id',
                    'FROM entity_table e',
                    'JOIN value_table v  ON v.data_id = e.data_id   <- tensile',
                    'JOIN value_table v2 ON v2.data_id = e.data_id  <- Mo',
                    'WHERE v.property_id = 22  AND CAST(v.value) BETWEEN 500.0 AND 700.0',
                    '  AND v2.property_id = 76  AND CAST(v2.value) > 0.1',
                ],
                'tags': ['2 JOIN', 'BETWEEN', 'PRECISE!', 'CASTx2'],
                'result_count': '1 *', 'source_count': '1',
                'source_info': '钛合金数据模型 (Ti-31 近alpha型钛合金)',
                'fields': [
                    ('材料牌号 / 类型', 'Ti-31 / 近alpha型钛合金', False),
                    ('[MATCH] 抗拉强度', '637 MPa', True),
                    ('[MATCH] Mo 含量', '0.6~1.2 wt%', True),
                    ('Al / 加工工艺', '2.5~3.2% / 退火', False),
                ],
                'data_title': '钛合金数据模型 (唯一匹配结果)'
            },
        ]
    },
    {
        'name': '聚合问题 (跨多数据源广域检索)',
        'label': '[C]',
        'subtitle': '双 JOIN . 元素成分约束 . 跨 15~30 个数据源',
        'color': C_AGG,
        'samples': [
            {
                'id': '#31', 'query': 'Ti含量大于0, Si含量还大于0.5的铝合金',
                'query_en': 'Al alloys: Ti > 0 AND Si > 0.5?',
                'sql_lines': [
                    'SELECT DISTINCT e.data_id',
                    'FROM entity_table e',
                    'JOIN value_table v  ON v.data_id = e.data_id   <- Ti',
                    'JOIN value_table v2 ON v2.data_id = e.data_id  <- Si',
                    'WHERE v.property_id = 56  AND CAST(v.value) > 0.0',
                    '  AND v2.property_id = 48  AND CAST(v2.value) > 0.5',
                ],
                'tags': ['2 JOIN', '15 data sources', '双条件', 'CASTx2'],
                'result_count': '40', 'source_count': '15',
                'source_info': '钢-硬度/弹性模量/电阻率/泊松比/热扩散率/拉伸/屈服/伸长率/晶粒组织 + 高强铝合金应力腐蚀 等',
                'fields': [
                    ('钢号 / 编号', 'R-26 / 580', False),
                    ('[MATCH] Ti 含量', '0.46 %', True),
                    ('[MATCH] Si 含量', '0.55 %', True),
                    ('Ni / Cr', '37.04% / 19.88%', False),
                ],
                'data_title': '钢-硬质合金_580 (跨15个数据集)'
            },
            {
                'id': '#88', 'query': '那些数据Cr含量大于0.1, 锰还大于0.5',
                'query_en': 'Cr > 0.1 AND Mn > 0.5?',
                'sql_lines': [
                    'SELECT DISTINCT e.data_id',
                    'FROM entity_table e',
                    'JOIN value_table v  ON v.data_id = e.data_id   <- Cr',
                    'JOIN value_table v2 ON v2.data_id = e.data_id  <- Mn',
                    'WHERE v.property_id = 58  AND CAST(v.value) > 0.1',
                    '  AND v2.property_id = 59  AND CAST(v2.value) > 0.5',
                ],
                'tags': ['2 JOIN', '30 data sources', '广域扫描', 'CASTx2'],
                'result_count': '563', 'source_count': '30',
                'source_info': '钢-硬度/力学性能/弹性模量/电阻率/泊松比/热扩散率/比热/晶粒组织 + RPV辐照压痕 + SCC应力腐蚀 等',
                'fields': [
                    ('钢号', '5Cr4Mo3SiMnVAl', False),
                    ('[MATCH] Cr 含量', '4.19 %', True),
                    ('[MATCH] Mn 含量', '1.14 %', True),
                    ('硬度 / 温度', '345.0 HV / 650C', False),
                ],
                'data_title': '钢-硬质合金_986 (跨30个数据集)'
            },
            {
                'id': '#96', 'query': '磷小于1, 硫也小于0.1的数据有哪些',
                'query_en': 'P < 1 AND S < 0.1?',
                'sql_lines': [
                    'SELECT DISTINCT e.data_id',
                    'FROM entity_table e',
                    'JOIN value_table v  ON v.data_id = e.data_id   <- P',
                    'JOIN value_table v2 ON v2.data_id = e.data_id  <- S',
                    'WHERE v.property_id = 49  AND CAST(v.value) < 1.0',
                    '  AND v2.property_id = 50  AND CAST(v2.value) < 0.1',
                ],
                'tags': ['2 JOIN', '27 data sources', '上限约束', 'CASTx2'],
                'result_count': '1162', 'source_count': '27',
                'source_info': '钢-拉伸/屈服/伸长率/弹性模量/硬度/电阻率/泊松比/热扩散率/比热/晶粒组织 + RPV辐照压痕 + SCC 等',
                'fields': [
                    ('材料编号 / 类别', 'A5083(1号) / RPV钢', False),
                    ('[MATCH] P 含量', '0.005', True),
                    ('[MATCH] S 含量', '0.002', True),
                    ('辐照温度 / 剂量', '290C / 2.26 dpa', False),
                ],
                'data_title': 'RPV材料辐照压痕 (跨27个数据集)'
            },
        ]
    },
]

# ===== LAYOUT =====
CARD_W = 11.2
CARD_H = 7.6
HEADER_H = 0.7
GAP_X = 0.6
GAP_Y = 0.8
TOP_MARGIN = FIG_H - 2.2
LEFT_MARGIN = 0.6

y_start = TOP_MARGIN

for cat_idx, cat in enumerate(categories):
    cat_y = y_start
    draw_text(ax, LEFT_MARGIN + 0.1, cat_y + 0.3,
              f'{cat["label"]} {cat["name"]}  --  {cat["subtitle"]}',
              size=15, color=cat['color'], bold=True)

    card_y = cat_y - CARD_H - 0.3
    for i, sample in enumerate(cat['samples']):
        card_x = LEFT_MARGIN + i * (CARD_W + GAP_X)

        # Card background
        draw_rounded_box(ax, card_x, card_y, CARD_W, CARD_H, color=C_WHITE)

        # Card header
        draw_header_bar(ax, card_x + 0.15, card_y + CARD_H - HEADER_H - 0.15,
                        CARD_W - 0.3, HEADER_H,
                        f"Sample {sample['id']}  {sample['query']}",
                        cat['color'], size=10.5)

        # English query
        draw_text(ax, card_x + 0.35, card_y + CARD_H - HEADER_H - 0.6,
                  sample['query_en'], size=7.8, color=C_TEXT_SEC, va='top')

        # SQL box
        sql_y = card_y + CARD_H - HEADER_H - 2.6
        sql_h = len(sample['sql_lines']) * 0.27 + 0.3
        draw_sql_box(ax, card_x + 0.3, sql_y, CARD_W - 0.6, sql_h,
                     sample['sql_lines'], size=6.8)

        # Tags
        tag_x_base = card_x + 0.35
        tag_y = sql_y - 0.6
        tag_x = tag_x_base
        for j, tag_text in enumerate(sample['tags']):
            tag_w = len(tag_text) * 0.15 + 0.4
            if 'data sources' in tag_text:
                tag_bg, tag_tc = C_AGG, 'white'
            elif 'PRECISE' in tag_text:
                tag_bg, tag_tc = C_RED, 'white'
            elif 'BETWEEN' in tag_text:
                tag_bg, tag_tc = '#a29bfe', 'white'
            elif 'JOIN' in tag_text:
                tag_bg, tag_tc = '#fd79a8', 'white'
            elif '等值' in tag_text:
                tag_bg, tag_tc = '#ffeaa7', C_TEXT
            elif '广域' in tag_text:
                tag_bg, tag_tc = C_AGG, 'white'
            else:
                tag_bg, tag_tc = '#dfe6e9', C_TEXT
            tag_rect = FancyBboxPatch((tag_x, tag_y), tag_w, 0.35,
                                      boxstyle="round,pad=0,rounding_size=0.1",
                                      facecolor=tag_bg, edgecolor='none', zorder=4)
            ax.add_patch(tag_rect)
            draw_text(ax, tag_x + tag_w/2, tag_y + 0.17, tag_text,
                      size=6.5, color=tag_tc, ha='center', bold=True)
            tag_x += tag_w + 0.12

        # Stats
        stats_y = tag_y - 0.5
        draw_text(ax, card_x + 0.35, stats_y,
                  f'Results: {sample["result_count"]}  |  Sources: {sample["source_count"]}',
                  size=7.5, color=C_TEXT_SEC)

        # Data section
        data_y = stats_y - 0.85
        draw_text(ax, card_x + 0.35, data_y + 0.25,
                  f'Data: {sample["data_title"]}', size=7, color=C_TEXT, bold=True)

        field_h = 0.42
        for k, (fname, fval, is_match) in enumerate(sample['fields']):
            fy = data_y - (k + 1) * field_h
            fw_name = 2.8
            # Field name
            draw_text(ax, card_x + 0.5, fy + field_h/2,
                      fname, size=7.2, color=C_TEXT_SEC, va='center')
            # Field value
            if is_match:
                fw_val = CARD_W - 1.5 - fw_name
                hl_rect = FancyBboxPatch(
                    (card_x + 0.5 + fw_name + 0.1, fy + 0.02),
                    fw_val, field_h - 0.04,
                    boxstyle="round,pad=0,rounding_size=0.08",
                    facecolor=C_HIGHLIGHT, edgecolor=C_HIGHLIGHT_BORDER,
                    linewidth=0.8, zorder=3)
                ax.add_patch(hl_rect)
                draw_text(ax, card_x + 0.5 + fw_name + 0.4, fy + field_h/2,
                          f'{fval}  [OK]', size=8.5, color=C_RED, va='center', bold=True)
            else:
                draw_text(ax, card_x + 0.5 + fw_name + 0.4, fy + field_h/2,
                          fval, size=7.5, color=C_TEXT, va='center')

        # Source info
        draw_text(ax, card_x + 0.35, card_y + 0.35,
                  f'Sources: {sample["source_info"][:80]}',
                  size=6.3, color=C_TEXT_SEC, va='center')

    y_start = card_y - GAP_Y


# ===== SUMMARY TABLE =====
table_y = y_start - 1.0
table_h = 2.6
table_w = FIG_W - 2 * LEFT_MARGIN
table_x = LEFT_MARGIN

draw_rounded_box(ax, table_x, table_y, table_w, table_h, color=C_WHITE)
draw_text(ax, table_x + table_w/2, table_y + table_h - 0.4,
          '三类问题对比总结', size=14, color=C_TEXT, ha='center', bold=True)

col_w = table_w / 4
headers = ['维度', '[A] 简单问题', '[B] 复杂问题', '[C] 聚合问题']
col_colors = ['#dfe6e9', C_SIMPLE, C_COMPLEX, C_AGG]
rows = [
    ['SQL JOIN 数', '1', '2', '2'],
    ['约束条件', '单一属性 (>=/<=/BETWEEN/=)', '双属性联合 (BETWEEN+range)', '双属性联合 (元素约束)'],
    ['典型数据源数', '1 ~ 6', '1 ~ 4', '15 ~ 30'],
    ['典型结果数', '21 ~ 58', '1 ~ 65 (极精准)', '40 ~ 1162 (广域)'],
    ['SQL 特征', 'CAST / 精确等值', 'BETWEEN + CASTx2', 'CASTx2 + 全库扫描'],
]

row_h = 0.35
start_y = table_y + table_h - 1.0
for col_i, hdr in enumerate(headers):
    rect = plt.Rectangle((table_x + col_w * col_i, start_y), col_w, row_h,
                         facecolor=col_colors[col_i], edgecolor='white', linewidth=0.5,
                         alpha=0.85 if col_i > 0 else 0.5, zorder=3)
    ax.add_patch(rect)
    draw_text(ax, table_x + col_w * col_i + col_w/2, start_y + row_h/2,
              hdr, size=10, color='white' if col_i > 0 else C_TEXT, ha='center', bold=True)

for row_i, row in enumerate(rows):
    ry = start_y - (row_i + 1) * row_h
    for col_i, val in enumerate(row):
        bg = '#f8f9fa' if row_i % 2 == 0 else C_WHITE
        rect = plt.Rectangle((table_x + col_w * col_i, ry), col_w, row_h,
                             facecolor=bg, edgecolor='#eee', linewidth=0.3, zorder=2)
        ax.add_patch(rect)
        draw_text(ax, table_x + col_w * col_i + col_w/2, ry + row_h/2,
                  val, size=8.5 if col_i > 0 else 9,
                  color=col_colors[col_i] if col_i > 0 else C_TEXT,
                  ha='center', bold=(col_i == 0))


# ===== FOOTER =====
footer_y = table_y - 0.5
draw_text(ax, FIG_W/2, footer_y,
          '数据来源: sample_queries_with_sql_100_new_with_data.json  |  '
          '黄色高亮 + [OK] = 符合查询约束的数值  |  2026-07-23',
          size=9.5, color=C_TEXT_SEC, ha='center')

# ===== SAVE =====
output_path = r'f:\Study\科研任务\论文\评测集\Code\sample\sample_quality_overview.png'
fig.savefig(output_path, dpi=180, bbox_inches='tight', facecolor=C_BG,
            edgecolor='none', pad_inches=0.3)
print(f'Saved to: {output_path}')
plt.close(fig)
print('Done!')
