import streamlit as st
import pandas as pd
import plotly.express as px
import backend
import lang_pack as lang
import calendar
from datetime import date, timedelta

# === 1. 页面配置 ===
st.set_page_config(
    page_title="My Ledger Pro",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="auto"
)

CURRENCY = "RM"
COLOR_MAP = {"收入": "#00CC96", "Income": "#00CC96", "支出": "#EF553B", "Expense": "#EF553B"}

# === 2. 核心 UI 样式 (智能响应式：电脑大气，手机紧凑) ===
st.markdown("""
    <style>
    /* --- 全局基础设置 --- */
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;}
    .block-container { padding-top: 1.5rem; padding-bottom: 3rem; }

    /* 顶部卡片 Metric (通用) */
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 15px;
        border-radius: 12px;
        box-shadow: none !important;
    }

    /* --- 日历组件 (默认：电脑端样式) --- */
    .calendar-container { width: 100%; }

    .cal-table { 
        width: 100%; 
        table-layout: fixed; /* 保持列宽一致 */
        border-spacing: 6px; /* 电脑端格子间距大一点 */
        border-collapse: separate;
    }

    .cal-th { 
        text-align: center; padding: 10px 0; 
        font-size: 0.9rem; color: var(--text-color); opacity: 0.7; 
    }
    .cal-td { padding: 0; vertical-align: top; }

    /* 电脑端的大格子 */
    .cal-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 8px; 
        height: 100px; /* 💻 电脑端高度：舒舒服服的 100px */
        padding: 8px;
        display: flex; flex-direction: column; justify-content: space-between; align-items: center;
        transition: transform 0.2s;
    }
    .cal-card:hover { transform: translateY(-3px); border-color: var(--primary-color); }

    .cal-day-num { font-size: 1rem; font-weight: 600; align-self: flex-start; }
    .cal-val { font-size: 0.85rem; font-weight: bold; align-self: flex-end; }

    /* 颜色状态 */
    .cal-card.pos { background-color: rgba(0, 204, 150, 0.1); border: 1px solid rgba(0, 204, 150, 0.4); color: #00CC96; }
    .cal-card.neg { background-color: rgba(239, 85, 59, 0.1); border: 1px solid rgba(239, 85, 59, 0.4); color: #EF553B; }
    .cal-card.today { border: 2px solid #FFD700 !important; }


    /* ====================================================================
       📱 手机端强制覆盖 (当屏幕宽度小于 600px 时生效)
       ==================================================================== */
    @media only screen and (max-width: 600px) {

        .block-container { padding-top: 1rem; padding-left: 0.5rem; padding-right: 0.5rem; }

        /* 强制缩小日历表格 */
        .cal-table { 
            border-spacing: 2px !important; /* 手机端间距变小 */
        }

        .cal-th { font-size: 0.7rem; padding: 2px 0; }

        /* 手机端的小格子 */
        .cal-card {
            height: 50px !important; /* 📱 手机端高度：强制压扁到 50px */
            padding: 2px !important;
            border-radius: 4px;
        }

        /* 字体极小化 */
        .cal-day-num { font-size: 0.7rem; align-self: center; line-height: 1.2; }
        .cal-val { 
            font-size: 0.6rem; 
            align-self: center; 
            margin-top: -2px;
        }

        /* 手机上禁用悬停动效 (防止误触) */
        .cal-card:hover { transform: none; }
    }
    </style>
    """, unsafe_allow_html=True)


def save_callback():
    lang_code = st.session_state.get('language_code', 'CN')
    amt = st.session_state.get('input_amount', 0.0)
    cat = st.session_state.get(f'input_category_{lang_code}', "")
    typ = st.session_state.get('input_type', "")
    note = st.session_state.get('input_note', "")
    dt = st.session_state.get('input_date', date.today())
    active_id = st.session_state.get('active_ledger_id')

    if active_id and amt > 0 and cat:
        db_type = "Expense" if any(x in typ for x in ["支出", "Expense"]) else "Income"
        backend.save_record(active_id, dt, db_type, cat, amt, note)
        st.toast("✅ " + ("已保存!" if lang_code == 'CN' else "Saved!"))

        st.session_state['input_amount'] = 0.0
        st.session_state['input_note'] = ""
    elif amt <= 0:
        # 如果是因为按 Enter 触发但没填金额，不做处理或轻轻提醒
        pass


def add_cat_callback():
    new_c = st.session_state.get('new_cat_input')
    active_id = st.session_state.get('active_ledger_id')
    if active_id and new_c and backend.add_category(active_id, new_c):
        st.toast(f"Tag added: {new_c}")
        st.session_state['new_cat_input'] = ""


def del_cat_callback():
    del_c = st.session_state.get('del_cat_select')
    active_id = st.session_state.get('active_ledger_id')
    if active_id and del_c:
        backend.delete_category(active_id, del_c)
        st.toast(f"Tag removed: {del_c}")


# === 4. 日历函数 ===
def render_calendar_html(year, month, df_data, mode='Month', selected_date=None):
    daily_net = {}
    if not df_data.empty:
        df_calc = df_data.copy()
        inc_keys = ['收入', 'Income']
        df_calc['calc_amount'] = df_calc.apply(
            lambda x: x['amount'] if x['type'] in inc_keys else -x['amount'], axis=1
        )
        daily_net = df_calc.groupby('date')['calc_amount'].sum().to_dict()

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)

    if mode == 'Week':
        sel_dt = pd.to_datetime(selected_date).date()
        target_week = []
        for week in month_days:
            if sel_dt.day in week and week[week.index(sel_dt.day)] != 0:
                target_week = week
                break
        if not target_week:
            month_days = cal.monthdayscalendar(year, month)
        else:
            month_days = [target_week]

    week_days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    html = '<div class="calendar-container"><table class="cal-table"><thead><tr>'
    for w in week_days: html += f'<th class="cal-th">{w}</th>'
    html += '</tr></thead><tbody class="week-view" >' if mode == 'Week' else '<tbody>'
    today_str = str(date.today())

    for week in month_days:
        html += '<tr>'
        for day in week:
            if day == 0:
                html += '<td class="cal-td"></td>'
            else:
                current_date_str = f"{year}-{month:02d}-{day:02d}"
                val = daily_net.get(current_date_str, 0)
                card_class = "cal-card"
                if val > 0:
                    card_class += " pos"
                elif val < 0:
                    card_class += " neg"
                if current_date_str == today_str: card_class += " today"

                val_display = ""
                if val != 0:
                    prefix = "+" if val > 0 else ""
                    val_display = f'<span class="cal-val">{prefix}{val:,.0f}</span>'
                html += f'<td class="cal-td"><div class="{card_class}"><span class="cal-day-num">{day}</span>{val_display}</div></td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    return html


# === 5. Sidebar & Main ===
backend.init_db()
all_ledgers = backend.get_ledgers()
ledger_names = [L[1] for L in all_ledgers]
ledger_map = {L[1]: L[0] for L in all_ledgers}

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2920/2920349.png", width=50)
    st.markdown("### " + lang.T("sidebar_title"))
    st.radio("Language", ["CN", "EN"], horizontal=True, label_visibility="collapsed", key="language_code")

    if ledger_names:
        selected_ledger_name = st.selectbox(lang.T("current_ledger"), ledger_names)
        current_ledger_id = ledger_map[selected_ledger_name]
        st.session_state['active_ledger_id'] = current_ledger_id
    else:
        st.warning("⚠️ No Ledgers")
        current_ledger_id = None
        selected_ledger_name = None

    st.divider()
    with st.expander(lang.T("settings")):
        new_ledger_name = st.text_input(lang.T("create_ledger"), key="new_ledger_input", placeholder="Name...")
        if st.button("➕", use_container_width=True):
            if new_ledger_name and new_ledger_name not in ledger_names:
                backend.add_ledger(new_ledger_name)
                st.rerun()
        if ledger_names:
            ledger_to_del = st.selectbox(lang.T("del_ledger"), ledger_names, key="del_ledger_select")
            if st.button("🗑️", type="primary", use_container_width=True):
                backend.delete_ledger(ledger_map[ledger_to_del])
                st.rerun()

    if selected_ledger_name:
        with st.expander(lang.T("manage_cats")):
            current_categories = backend.get_categories(current_ledger_id)
            c1, c2 = st.tabs([lang.T("tab_add_cat"), lang.T("tab_del_cat")])
            with c1:
                st.text_input("New", key='new_cat_input', label_visibility="collapsed")
                st.button("Add", on_click=add_cat_callback, use_container_width=True)
            with c2:
                st.selectbox("Del", current_categories, key='del_cat_select', label_visibility="collapsed")
                st.button("Remove", on_click=del_cat_callback, type="primary", use_container_width=True)

if selected_ledger_name:
    st.title(f"{selected_ledger_name}")
else:
    st.title(lang.T("app_title"))
    st.stop()

# 记账区
with st.expander(lang.T("header_entry"), expanded=True):
    c1, c2, c3, c4 = st.columns([1.2, 1, 1.2, 1])
    with c1: st.date_input(lang.T("date"), date.today(), key='input_date')
    with c2:
        type_opts = ["支出", "收入"] if st.session_state.get('language_code') == 'CN' else ["Expense", "Income"]
        st.selectbox(lang.T("category"), type_opts, key='input_type', label_visibility="visible")
    with c3:
        current_cats = backend.get_categories(current_ledger_id)
        st.selectbox(lang.T("category"), current_cats, format_func=lang.get_cat_display,
                     key=f'input_category_{st.session_state.get("language_code")}')
    with c4:
        st.number_input(lang.T("amount"), min_value=0.0, step=1.0, format="%.2f",
                        key='input_amount', on_change=save_callback)

    st.text_input(lang.T("note"), key='input_note', placeholder="Note...", on_change=save_callback)
    st.button(lang.T("btn_save"), on_click=save_callback, type="primary", use_container_width=True)


raw_df = backend.get_all_records(current_ledger_id)

if not raw_df.empty:
    current_lang = st.session_state.get('language_code', 'CN')

    # 0. 清洗数据
    raw_df['category'] = raw_df['category'].astype(str).str.strip()

    if current_lang == 'EN':
        # 1. Type 翻译 (使用 Mapping 更稳健)
        type_map_en = {'收入': 'Income', '支出': 'Expense', 'Income': 'Income', 'Expense': 'Expense'}
        raw_df['type'] = raw_df['type'].map(type_map_en).fillna(raw_df['type'])

        # 2. Category 翻译
        raw_df['category'] = raw_df['category'].replace(lang.CAT_TRANS)

    else:

        type_map_cn = {'Income': '收入', 'Expense': '支出', '收入': '收入', '支出': '支出'}
        raw_df['type'] = raw_df['type'].map(type_map_cn).fillna(raw_df['type'])

        raw_df['category'] = raw_df['category'].replace(lang.CAT_TRANS_REV)
        raw_df['category'] = raw_df['category'].replace(lang.CAT_CN_EMOJI)

# 选项卡
tab_overview, tab_stats, tab_data, tab_report = st.tabs(
    [lang.T("tab_overview"), lang.T("tab_stats"), lang.T("tab_data"), lang.T("tab_report")])

if raw_df.empty:
    st.info(lang.T("empty"))
    st.stop()

# === Tab 1: 概览 ===
with tab_overview:
    inc_key = '收入' if current_lang == 'CN' else 'Income'
    exp_key = '支出' if current_lang == 'CN' else 'Expense'

    inc = raw_df[raw_df['type'] == inc_key]['amount'].sum()
    exp = raw_df[raw_df['type'] == exp_key]['amount'].sum()
    bal = inc - exp

    col1, col2, col3 = st.columns(3)
    col1.metric(lang.T("total_income"), f"{CURRENCY} {inc:,.2f}", delta="Income", delta_color="normal")
    col2.metric(lang.T("total_expense"), f"{CURRENCY} {exp:,.2f}", delta=f"-{exp:,.2f}", delta_color="normal")
    col3.metric(lang.T("balance"), f"{CURRENCY} {bal:,.2f}", delta=f"{bal:,.2f}", delta_color="normal")

    st.divider()
    c_chart1, c_chart2 = st.columns(2)
    with c_chart1:
        st.subheader("📊 " + ("收支构成" if current_lang == 'CN' else "Composition"))

        # 🔥 再次确保饼图数据是翻译过的
        df_pie = raw_df.copy()
        chart_data = df_pie.groupby('category')['amount'].sum().reset_index()

        fig_pie = px.pie(chart_data, values='amount', names='category', hole=0.5)
        st.plotly_chart(fig_pie, use_container_width=True)

    with c_chart2:
        st.subheader("📅 " + ("近期趋势" if current_lang == 'CN' else "Trend"))
        daily_trend = raw_df.groupby('date')['amount'].sum().reset_index()
        fig_line = px.area(daily_trend, x='date', y='amount')
        st.plotly_chart(fig_line, use_container_width=True)

# === Tab 2: 统计日历 ===
with tab_stats:
    cc1, cc2 = st.columns([1, 2])
    with cc1:
        v_mode_sel = st.radio(lang.T("cal_view"), [lang.T("view_month"), lang.T("view_week")], horizontal=True)
        mode_code = 'Month' if v_mode_sel == lang.T("view_month") else 'Week'
    with cc2: pick_date = st.date_input(lang.T("cal_date"), date.today())

    st.divider()
    cal_html = render_calendar_html(pick_date.year, pick_date.month, raw_df, mode=mode_code, selected_date=pick_date)
    st.markdown(cal_html, unsafe_allow_html=True)

    st.divider()
    df_viz = raw_df.copy()
    df_viz['month'] = pd.to_datetime(df_viz['date']).dt.to_period('M').astype(str)
    monthly_stats = df_viz.groupby(['month', 'type'])['amount'].sum().reset_index()
    fig_bar = px.bar(monthly_stats, x='month', y='amount', color='type', barmode='group', color_discrete_map=COLOR_MAP)
    st.plotly_chart(fig_bar, use_container_width=True)

# === Tab 3: 明细 ===
with tab_data:
    with st.expander(lang.T("filter_label"), expanded=False):
        f1, f2 = st.columns(2)
        available_cats = raw_df['category'].unique().tolist()
        sel_cats = f1.multiselect(lang.T("filter_cat"), available_cats)

        type_opts = [lang.T("all")] + (
            [lang.T("Expense"), lang.T("Income")] if current_lang == 'EN' else ["支出", "收入"])
        sel_type = f2.selectbox(lang.T("filter_type"), type_opts)

    df_show = raw_df.copy()
    if sel_cats: df_show = df_show[df_show['category'].isin(sel_cats)]
    if sel_type != lang.T("all"):
        target_type = sel_type
        df_show = df_show[df_show['type'] == target_type]

    st.dataframe(
        df_show,
        use_container_width=True,
        hide_index=True,
        column_order=("date", "type", "category", "amount", "note"),
        column_config={
            "date": st.column_config.DateColumn(lang.T("date"), format="YYYY-MM-DD"),
            "type": st.column_config.TextColumn(lang.T("type"), width="small"),
            "category": st.column_config.TextColumn(lang.T("category"), width="medium"),
            "amount": st.column_config.NumberColumn(lang.T("amount"), format=f"{CURRENCY} %.2f", step=0.01),
            "note": st.column_config.TextColumn(lang.T("note"), width="large"),
        }
    )

    c_del1, c_del2 = st.columns([3, 1])
    with c_del1:
        del_opts = {f"{r['date']} - {r['category']} - {r['amount']}": r['id'] for i, r in df_show.iterrows()}
        sel_rec_label = st.selectbox("Delete Record", options=list(del_opts.keys()), label_visibility="collapsed")
    with c_del2:
        if st.button("🗑️ " + lang.T("tab_del"), type="secondary", use_container_width=True):
            if sel_rec_label:
                backend.delete_record(del_opts[sel_rec_label])
                st.rerun()

# === Tab 4: 财务报告 (专业版：去 Emoji + 收支分列) ===
with tab_report:
    st.subheader(lang.T("report_type"))
    report_mode = st.radio("Mode", [lang.T("rep_weekly"), lang.T("rep_monthly"), lang.T("rep_yearly")], horizontal=True,
                           label_visibility="collapsed")

    start_date, end_date = None, None
    filter_desc = ""

    c_rep1, c_rep2 = st.columns(2)
    with c_rep1:
        if report_mode == lang.T("rep_weekly"):
            sel_d = st.date_input(lang.T("sel_week"), date.today())
            start_date = sel_d - timedelta(days=sel_d.weekday())
            end_date = start_date + timedelta(days=6)
            filter_desc = f"Week: {start_date} ~ {end_date}"
        elif report_mode == lang.T("rep_monthly"):
            sel_d = st.date_input(lang.T("sel_month"), date.today())
            start_date = sel_d.replace(day=1)
            next_month = start_date.replace(day=28) + timedelta(days=4)
            end_date = next_month - timedelta(days=next_month.day)
            filter_desc = f"Month: {start_date.strftime('%Y-%m')}"
        elif report_mode == lang.T("rep_yearly"):
            sel_year = st.selectbox(lang.T("sel_year"), range(date.today().year, 2020, -1))
            start_date = date(sel_year, 1, 1)
            end_date = date(sel_year, 12, 31)
            filter_desc = f"Year: {sel_year}"

    if start_date and end_date:
        mask = (pd.to_datetime(raw_df['date']).dt.date >= start_date) & (
                pd.to_datetime(raw_df['date']).dt.date <= end_date)
        rep_df = raw_df[mask].copy()

        st.divider()
        st.markdown(f"### 📄 {filter_desc}")

        if not rep_df.empty:
            inc_k = '收入' if current_lang == 'CN' else 'Income'
            exp_k = '支出' if current_lang == 'CN' else 'Expense'

            r_inc = rep_df[rep_df['type'] == inc_k]['amount'].sum()
            r_exp = rep_df[rep_df['type'] == exp_k]['amount'].sum()
            r_bal = r_inc - r_exp

            rc1, rc2, rc3 = st.columns(3)
            rc1.metric(lang.T("total_income"), f"{CURRENCY} {r_inc:,.2f}")
            rc2.metric(lang.T("total_expense"), f"{CURRENCY} {r_exp:,.2f}")
            rc3.metric(lang.T("balance"), f"{CURRENCY} {r_bal:,.2f}")

            # === 页面展示：分类汇总 ===
            st.subheader(lang.T("cat_breakdown"))
            cat_summary = rep_df.groupby(['category', 'type'])['amount'].sum().reset_index().sort_values('amount',
                                                                                                         ascending=False)
            st.dataframe(
                cat_summary,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "category": st.column_config.TextColumn(lang.T("category")),
                    "type": st.column_config.TextColumn(lang.T("type")),
                    "amount": st.column_config.NumberColumn(lang.T("amount"), format=f"{CURRENCY} %.2f")
                }
            )

            # === 页面展示：明细 ===
            st.subheader(lang.T("tab_data"))
            st.dataframe(
                rep_df,
                use_container_width=True,
                hide_index=True,
                column_order=("date", "type", "category", "amount", "note"),
                column_config={
                    "date": st.column_config.DateColumn(lang.T("date"), format="YYYY-MM-DD"),
                    "type": st.column_config.TextColumn(lang.T("type")),
                    "category": st.column_config.TextColumn(lang.T("category")),
                    "amount": st.column_config.NumberColumn(lang.T("amount"), format=f"{CURRENCY} %.2f"),
                    "note": st.column_config.TextColumn(lang.T("note"))
                }
            )

            export_df = rep_df.copy()

            # 1. 清洗 Emoji (保持不变)
            def clean_emoji(val):
                if isinstance(val, str) and " " in val:
                    parts = val.split(" ", 1)
                    if len(parts) > 1:
                        return parts[1]
                return val


            export_df['category'] = export_df['category'].apply(clean_emoji)

            # 2. 收支分列 (保持单币种 amount, 空值设为 None)
            export_df[lang.T('col_inc')] = export_df.apply(lambda x: x['amount'] if x['type'] == inc_k else None,
                                                           axis=1)
            export_df[lang.T('col_exp')] = export_df.apply(lambda x: x['amount'] if x['type'] == exp_k else None,
                                                           axis=1)

            # 3. 整理列
            final_cols = ['date', 'category', lang.T('col_inc'), lang.T('col_exp'), 'note']
            export_df = export_df[final_cols]

            # 4. 重命名列头 (方便后续操作)
            col_date = lang.T('col_date')
            col_cat = lang.T('col_cat')
            col_inc = lang.T('col_inc')
            col_exp = lang.T('col_exp')
            col_note = lang.T('col_note')

            export_df.columns = [col_date, col_cat, col_inc, col_exp, col_note]


            # 第一步：计算原始总和
            sum_inc = export_df[col_inc].sum()
            sum_exp = export_df[col_exp].sum()

            diff = 0
            balancing_row = pd.DataFrame()
            final_total = 0

            # 第二步：判断哪边少，就在哪边补
            if sum_inc > sum_exp:
                # 收入 > 支出 (盈利)：需要在【支出列】补平
                diff = sum_inc - sum_exp
                final_total = sum_inc  # 最终平衡总额以大者为准

                balancing_row = pd.DataFrame([{
                    col_date: None,
                    col_cat: "c.c",  # 用户要求的名称
                    col_inc: None,
                    col_exp: diff,  # 补在支出
                    col_note: "Balancing Figure"
                }])

            elif sum_exp > sum_inc:
                # 支出 > 收入 (亏损)：需要在【收入列】补平
                diff = sum_exp - sum_inc
                final_total = sum_exp  # 最终平衡总额以大者为准

                balancing_row = pd.DataFrame([{
                    col_date: None,
                    col_cat: "c.c",
                    col_inc: diff,  # 补在收入
                    col_exp: None,
                    col_note: "Balancing Figure"
                }])

            else:
                # 刚好相等
                final_total = sum_inc

            # 第三步：如果有差额，插入平衡行
            if diff > 0 and not balancing_row.empty:
                export_df = pd.concat([export_df, balancing_row], ignore_index=True)

            # 第四步：添加最终的 TOTAL 行 (两边金额现在一定相等)
            total_row = pd.DataFrame([{
                col_date: "TOTAL",
                col_cat: "",
                col_inc: final_total,
                col_exp: final_total,
                col_note: "Balanced"
            }])

            export_df = pd.concat([export_df, total_row], ignore_index=True)

            # ==========================================
            # 🔴 结束修改
            # ==========================================

            excel_data = backend.to_excel(export_df)

            st.download_button(
                label=f"{lang.T('download_excel')}",
                data=excel_data,
                file_name=f'Financial_Report_{start_date}_{end_date}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                type='primary'
            )