# -*- coding: utf-8 -*-
"""Generate compact paper figure: paired-property relationship overview."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
import numpy as np

plt.rcParams['font.family'] = ['SimSun', 'SimHei', 'Times New Roman', 'sans-serif']
plt.rcParams['font.sans-serif'] = ['SimHei', 'SimSun', 'Microsoft YaHei']
plt.rcParams['font.size'] = 8
plt.rcParams['axes.unicode_minus'] = False

# ── Colors ──
WHITE   = '#FFFFFF'
BLACK   = '#1a1a1a'
GRAY    = '#666666'
LGRAY   = '#e8e8e8'
BG      = '#fafafa'
C_A     = '#2E7D52'
C_B     = '#1A5C8A'
C_C     = '#5B3E96'
A_LIGHT = '#E8F5E9'
B_LIGHT = '#E3F0F8'
C_LIGHT = '#EDE7F6'
MATCH   = '#FFF3CD'
MATCH_B = '#E6A817'

# ── Figure (compact width for paper) ──
FIG_W = 7.0   # inches (~17.8 cm)
DPI   = 300

# ── SAMPLE DATA ──
# Each: (id, category_label, cat_color, cat_light,
#         query_cn, prop_a, val_a, prop_b, val_b, result_n, src_n, sql_feature)
samples = [
    # ---- Simple ----
    ('21', 'A', C_A, A_LIGHT,
     '硬度 > 200',
     '硬度', '269 HB', None, None,
     '58', '3', '1 JOIN, >'),
    ('52', 'A', C_A, A_LIGHT,
     '屈服强度 400~800 MPa',
     '屈服强度', '743 MPa', None, None,
     '55', '3', '1 JOIN, BETWEEN'),
    ('62', 'A', C_A, A_LIGHT,
     '伸长率 = 16%',
     '伸长率', '16%', None, None,
     '21', '6', '1 JOIN, ='),
    # ---- Complex ----
    ('1',  'B', C_B, B_LIGHT,
     '晶粒体积 > 50000\n且半径 > 15',
     '体积', '52925', '半径', '23.3',
     '20', '1', '2 JOIN'),
    ('18', 'B', C_B, B_LIGHT,
     'Co 40~60% 且 W > 2%\n(钴基高温合金)',
     'Co', '43.1%', 'W', '2.8%',
     '65', '4', '2 JOIN, BETWEEN'),
    ('50', 'B', C_B, B_LIGHT,
     '抗拉 500~700 MPa\n且 Mo > 0.1%',
     '抗拉强度', '637 MPa', 'Mo', '0.6~1.2%',
     '1', '1', '2 JOIN, BETWEEN'),
    # ---- Multi-Source ----
    ('31', 'C', C_C, C_LIGHT,
     'Ti > 0% 且 Si > 0.5%\n(铝合金)',
     'Ti', '0.46%', 'Si', '0.55%',
     '40', '15', '2 JOIN, 跨15源'),
    ('88', 'C', C_C, C_LIGHT,
     'Cr > 0.1% 且 Mn > 0.5%',
     'Cr', '4.19%', 'Mn', '1.14%',
     '563', '30', '2 JOIN, 跨30源'),
    ('96', 'C', C_C, C_LIGHT,
     'P < 1 且 S < 0.1',
     'P', '0.005', 'S', '0.002',
     '1162', '27', '2 JOIN, 跨27源'),
]

N = len(samples)  # 9

def T(ax, x, y, s, size=8, color=BLACK, ha='left', va='center', bold=False, family=None):
    ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va,
            fontweight='bold' if bold else 'normal',
            fontfamily=family or plt.rcParams['font.family'])

# ── LAYOUT ──
# Compact table: 1 header row + 9 sample rows + 1 category sub-header rows
# Width: ~6.5 inches of content

MARGIN = 0.25
CONTENT_W = FIG_W - 2*MARGIN

# Column widths:
COL_CAT  = 0.28
COL_ID   = 0.30
COL_QUERY = 1.6
COL_ARROW = 0.65  # property a value + arrow to property b
COL_PROP_A = 0.85
COL_VAL_A  = 0.75
COL_ARROW_MID = 0.35  # connector
COL_PROP_B = 0.80
COL_VAL_B  = 0.75
COL_SQL  = 1.0
COL_N    = 0.35
COL_SRC  = 0.35

# Actually, let me use a simpler fixed layout.
# I'll compute x positions manually for a cleaner result.

ROW_H = 0.32
SEP_H = 0.04
HEADER_H = 0.28
TITLE_H = 0.4

# x positions (relative to LEFT edge)
LEFT = MARGIN
x_cat   = LEFT + 0.05          # category marker
x_id    = LEFT + 0.35          # sample ID
x_query = LEFT + 0.75          # query text
x_arrow = LEFT + 2.55          # "propA = valA"
# For single-property: propA + valA centered
# For dual-property: propA + valA --> propB + valB
x_prop_a_end = LEFT + 4.15     # where prop_a value ends
x_link  = LEFT + 4.25          # "-->" or space
x_prop_b_start = LEFT + 4.50   # where prop_b starts
x_prop_b_end = LEFT + 5.55     # where prop_b value ends
x_sql   = LEFT + 5.70          # SQL features
x_n     = LEFT + 6.40          # result count
x_src   = LEFT + 6.70          # source count

# Simpler approach: just 5 main columns
# | Cat+ID | Query | Matched Property A | -> | Matched Property B | SQL特征 | N | Src |
COL0_W = 0.72  # cat + id
COL1_W = 1.70  # query
COL2_W = 1.65  # property A value [+ arrow + property B value]
COL3_W = 1.10  # SQL feature tags
COL4_W = 0.45  # N results
COL5_W = 0.38  # Src count

x0 = LEFT
x1 = x0 + COL0_W
x2 = x1 + COL1_W
x3 = x2 + COL2_W
x4 = x3 + COL3_W
x5 = x4 + COL4_W
x6 = x5 + COL5_W

# Compute total height
total_rows = N + 4  # 9 samples + 3 sub-headers + 1 main header + title area
FIG_H = 1.0 + 1.0 * 0.32 + 3 * 0.04 + N * ROW_H + 0.5  # title + header + gaps + rows + footer
# Actually let me compute properly
FIG_H = TITLE_H + HEADER_H + N * ROW_H + 3 * SEP_H + 0.6  # 0.6 for footer
# ~ 0.4 + 0.28 + 9*0.32 + 0.12 + 0.6 = 0.4+0.28+2.88+0.12+0.6 = 4.28 inches

fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor=WHITE)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis('off')

# ── TITLE ──
y = FIG_H - 0.2
T(ax, FIG_W/2, y, '图X  评测集典型样本的属性关系展示', size=9.5, bold=True, ha='center', family='SimHei')
y -= TITLE_H

# ── TABLE HEADER ──
cols_info = [
    (x0, x1-x0, '类别/编号'),
    (x1, x2-x1, '自然语言查询'),
    (x2, x3-x2, '匹配属性及数值'),
    (x3, x4-x3, 'SQL 特征'),
    (x4, x5-x4, 'N'),
    (x5, x6-x5, '源'),
]
for cx, cw, label in cols_info:
    ax.add_patch(Rectangle((cx, y-HEADER_H), cw, HEADER_H,
                           facecolor='#f2f2f2', edgecolor='#cccccc', lw=0.3, zorder=3))
    T(ax, cx+cw/2, y-HEADER_H/2, label, size=7.2, bold=True, ha='center', family='SimHei')

# Vertical grid lines
for cx in [x1, x2, x3, x4, x5]:
    ax.plot([cx, cx], [y-HEADER_H, 0], color='#e0e0e0', lw=0.3, zorder=1)

y -= HEADER_H

# ── CATEGORY SUB-HEADERS & SAMPLES ──
prev_cat = None
for idx, s in enumerate(samples):
    sid, cat, cat_c, cat_l, query, pa, va, pb, vb, rn, sn, sql_f = s

    # Category separator
    if cat != prev_cat:
        cat_names = {'A': 'A. 简单问题 (单属性过滤)', 'B': 'B. 复杂问题 (双属性联合约束)',
                     'C': 'C. 聚合问题 (跨多数据源检索)'}
        y -= SEP_H
        ax.add_patch(Rectangle((x0, y-0.04), x6-x0, 0.04, facecolor=cat_c, edgecolor='none', zorder=3))
        prev_cat = cat

    # Row background
    row_bg = WHITE if idx % 2 == 0 else '#fafafa'
    ax.add_patch(Rectangle((x0, y-ROW_H), x6-x0, ROW_H,
                           facecolor=row_bg, edgecolor='#e8e8e8', lw=0.25, zorder=2))

    # Col 0: Category + ID
    # Category dot
    ax.plot(x0 + 0.14, y - ROW_H/2, 'o', color=cat_c, markersize=5, zorder=4)
    T(ax, x0 + 0.30, y - ROW_H/2, f'#{sid}', size=8, bold=True, color=cat_c, family='SimHei')

    # Col 1: Query
    query_lines = query.split('\n')
    if len(query_lines) == 1:
        T(ax, x1 + 0.08, y - ROW_H/2, query, size=7.2, color=BLACK)
    else:
        T(ax, x1 + 0.08, y - 0.10, query_lines[0], size=7.2, color=BLACK)
        T(ax, x1 + 0.08, y - ROW_H + 0.10, query_lines[1], size=6.3, color=GRAY)

    # Col 2: Property values (the core relationship display)
    if pb is None:
        # Single property: just show propA = valA
        px_mid = x2 + (x3-x2)/2
        T(ax, px_mid, y - ROW_H/2, f'{pa} = {va}',
          size=7.5, bold=True, color=BLACK, ha='center')
    else:
        # Dual property: propA = valA  -->  propB = valB
        # Left block: propA = valA
        rect_w_a = (x3 - x2) * 0.42
        rect_x_a = x2 + 0.04
        rect_y_a = y - ROW_H + 0.04
        rect_h_a = ROW_H - 0.08
        ax.add_patch(Rectangle((rect_x_a, rect_y_a), rect_w_a, rect_h_a,
                               facecolor=MATCH, edgecolor=MATCH_B, lw=0.5, zorder=3))
        T(ax, rect_x_a + rect_w_a/2, y - ROW_H/2 + 0.06,
          f'{pa}', size=6.5, color=GRAY, ha='center')
        T(ax, rect_x_a + rect_w_a/2, y - ROW_H/2 - 0.06,
          f'{va}', size=7.5, bold=True, color='#C62828', ha='center')

        # Arrow
        arrow_x = rect_x_a + rect_w_a + 0.06
        arrow_w = (x3 - x2) * 0.12
        T(ax, arrow_x + arrow_w/2, y - ROW_H/2, '&', size=8, color=GRAY, ha='center', bold=True)

        # Right block: propB = valB
        rect_x_b = arrow_x + arrow_w + 0.06
        rect_w_b = (x3 - x2) * 0.42
        ax.add_patch(Rectangle((rect_x_b, rect_y_a), rect_w_b, rect_h_a,
                               facecolor=MATCH, edgecolor=MATCH_B, lw=0.5, zorder=3))
        T(ax, rect_x_b + rect_w_b/2, y - ROW_H/2 + 0.06,
          f'{pb}', size=6.5, color=GRAY, ha='center')
        T(ax, rect_x_b + rect_w_b/2, y - ROW_H/2 - 0.06,
          f'{vb}', size=7.5, bold=True, color='#C62828', ha='center')

    # Col 3: SQL features
    T(ax, x3 + 0.06, y - ROW_H/2, sql_f, size=6.5, color=GRAY)

    # Col 4: N results
    T(ax, x4 + (x5-x4)/2, y - ROW_H/2, rn, size=7.5, bold=True, color=BLACK, ha='center')

    # Col 5: Source count
    T(ax, x5 + (x6-x5)/2, y - ROW_H/2, sn, size=7.2, color=GRAY, ha='center')

    y -= ROW_H

# ── FOOTER ──
y -= 0.15
T(ax, FIG_W/2, y,
  '注: 黄色底为匹配查询条件的数值; N=结果数量, 源=覆盖数据源数. 数据来自 sample_queries_with_sql_100_new_with_data.json',
  size=6.5, color=GRAY, ha='center', family='SimSun')
y -= 0.15
T(ax, FIG_W/2, y,
  '简单问题=单属性过滤; 复杂问题=双属性联合约束; 聚合问题=跨多数据源检索(15~30个数据源).',
  size=6.5, color=GRAY, ha='center', family='SimSun')

# ── SAVE ──
output_path = r'f:\Study\科研任务\论文\评测集\Code\sample\sample_quality_overview.png'
fig.savefig(output_path, dpi=DPI, bbox_inches='tight', facecolor=WHITE,
            edgecolor='none', pad_inches=0.1)
print(f'OK: {FIG_W}\" x {FIG_H:.1f}\" @ {DPI} DPI')
plt.close(fig)
