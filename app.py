import streamlit as st
import pandas as pd
import datetime
import os

st.set_page_config(page_title="美舒容雲端洗衣管理系統", layout="wide")

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 歡迎使用洗衣店管理系統")
    pwd = st.text_input("請輸入管理密碼：", type="password")
    if st.button("登入系統"):
        if pwd == "1234":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("❌ 密碼錯誤！")
    st.stop()

# ==================== 🔓 登入成功 ====================
O_FILE = "laundry_orders.csv"
C_FILE = "laundry_customers.csv"

PRICE_LIST = {"一般襯衫/T恤": 50, "長褲/牛仔褲": 60, "厚外套/大衣": 150, "床單/被套": 200, "毛毯/特殊材質": 300}

if os.path.exists(O_FILE):
    df_orders = pd.read_csv(O_FILE)
    df_orders["手機號碼"] = df_orders["手機號碼"].astype(str)
else:
    df_orders = pd.DataFrame(columns=["訂單編號", "日期", "顧客姓名", "手機號碼", "衣服項目", "數量", "花色備註", "洗法備註", "前次餘額", "總金額", "目前狀態", "付款方式", "現有餘額"])

if os.path.exists(C_FILE):
    df_cust = pd.read_csv(C_FILE)
    df_cust["手機號碼"] = df_cust["手機號碼"].astype(str)
else:
    df_cust = pd.DataFrame(columns=["手機號碼", "顧客姓名", "性別", "儲值餘額", "折扣比率"])

if "receipt_data" not in st.session_state:
    st.session_state.receipt_data = None

def get_cust(phone):
    if df_cust.empty:
        return None, 0, 0
    match = df_cust[df_cust["手機號碼"] == str(phone)]
    if not match.empty:
        return match.iloc[0]["顧客姓名"], int(match.iloc[0]["儲值餘額"]), int(match.iloc[0]["折扣比率"])
    return None, 0, 0

t1, t2, t3, t4 = st.tabs(["📥 洗衣作業", "📋 清洗進度看板", "🔍 客戶資料維護", "📊 報表與統計"])

with t1:
    col1, col2 = st.columns(2)
    with col1:
        st.header("💰 會員儲值與開戶")
        with st.form("f_dep"):
            c_phone = st.text_input("會員手機號碼").strip()
            c_name = st.text_input("會員姓名")
            c_gender = st.radio("性別", ["男", "女"], horizontal=True)
            c_discount = st.number_input("折扣比率 (%)", min_value=0, value=0)
            amount = st.number_input("儲值金額 (元)", min_value=0, value=0)
            if st.form_submit_button("執行儲值 / 開戶存檔"):
                if not c_phone:
                    st.error("❌ 請輸入手機號碼")
                else:
                    if not df_cust.empty and str(c_phone) in df_cust["手機號碼"].values:
                        idx = df_cust[df_cust["手機號碼"] == str(c_phone)].index
                        df_cust.at[idx[0], "儲值餘額"] += amount
                        df_cust.at[idx[0], "折扣比率"] = c_discount
                    else:
                        new_c = {"手機號碼": str(c_phone), "顧客姓名": c_name, "性別": c_gender, "儲值餘額": int(amount), "折扣比率": int(c_discount)}
                        df_cust = pd.concat([df_cust, pd.DataFrame([new_c])], ignore_index=True)
                    df_cust.to_csv(C_FILE, index=False)
                    st.success("✅ 會員資料存檔成功！")
                    st.rerun()
    with col2:
        st.header("📥 門市收件作業")
        with st.form("f_ord", clear_on_submit=True):
            o_phone = st.text_input("顧客手機號碼").strip()
            c_name_m, c_bal_m, c_disc_m = get_cust(o_phone)
            if o_phone and c_name_m:
                st.caption(f"💡 會員：{c_name_m} ｜ 餘額：${c_bal_m} ｜ 折扣：{c_disc_m}%")
            selected_item = st.selectbox("衣服種類", list(PRICE_LIST.keys()))
            quantity = st.number_input("數量", min_value=1, value=1)
            opt_color = st.selectbox("花色/特徵", ["不分", "深色", "淺色", "白色", "黑色", "黃色", "藍(深藍)色", "粉紅/紅色"])
            opt_wash = st.selectbox("洗法/配件", ["水洗", "乾洗", "燙衣", "其他", "拉大", "重處理"])
            pay_method = st.radio("付款方式", ["儲值金扣款", "現金結帳"], horizontal=True)
            
            subtotal = PRICE_LIST[selected_item] * quantity
            discount_amount = int(subtotal * (c_disc_m / 100))
            total_price = subtotal - discount_amount
            st.info(f"💰 金額：原價 ${subtotal} - 折扣 ${discount_amount} = 應收 **${total_price}** 元")
            
            if st.form_submit_button("確認入庫 (收件)"):
                if not o_phone:
                    st.error("❌ 請輸入手機號碼")
                else:
                    can_order = True
                    cust_idx = df_cust[df_cust["手機號碼"] == str(o_phone)].index if not df_cust.empty else []
                    if pay_method == "儲值金扣款":
                        if len(cust_idx) == 0:
                            st.error("❌ 該手機非會員，請用現金結帳")
                            can_order = False
                        elif df_cust.at[cust_idx[0], "儲值餘額"] < total_price:
                            st.error("❌ 餘額不足")
                            can_order = False
                        else:
                            df_cust.at[cust_idx[0], "儲值餘額"] -= total_price
                            df_cust.to_csv(C_FILE, index=False)
                    if can_order:
                        final_name = c_name_m if c_name_m else "現場散客"
                        order_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                        today_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        _, updated_bal, _ = get_cust(o_phone)
                        new_order = {
                            "訂單編號": order_id, "日期": today_str, "顧客姓名": final_name, "手機號碼": str(o_phone),
                            "衣服項目": selected_item, "數量": quantity, "花色備註": opt_color, "洗法備註": opt_wash,
                            "前次餘額": c_bal_m, "總金額": total_price, "目前狀態": "待清洗", "付款方式": pay_method, "現有餘額": updated_bal
                        }
                        df_orders = pd.concat([df_orders, pd.DataFrame([new_order])], ignore_index=True)
                        df_orders.to_csv(O_FILE, index=False)
                        st.session_state.receipt_data = {"id": order_id, "date": today_str, "name": final_name, "phone": o_phone, "item": selected_item, "qty": quantity, "color": opt_color, "wash": opt_wash, "total": total_price, "pay": pay_method, "balance": updated_bal}
                        st.success("✅ 收件成功！")
                        st.rerun()

    if st.session_state.receipt_data:
        r = st.session_state.receipt_data
        st.markdown(f"""
        <div style="background-color: white; color: black; padding: 15px; border: 1px solid #ccc; max-width: 300px;">
            <h4>✨ 美舒容洗衣門市 ✨</h4>
            <p>單號: {r['id']}<br>日期: {r['date']}<br>客戶: {r['name']} ({r['phone']})<br>品項: {r['item']} x {r['qty']}<br>特徵洗法: {r['color']} / {r['wash']}<br>實收: ${r['total']} ({r['pay']})<br><b>帳戶餘額: ${r['balance']}</b></p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("關閉收據"):
            st.session_state.receipt_data = None
            st.rerun()

with t2:
    st.header("📋 門市衣物清洗狀態看板")
    if df_orders.empty:
        st.info("暫無訂單")
    else:
        sf = st.radio("篩選狀態", ["全部", "待清洗", "清洗中", "已完成（待取）", "已取件"], horizontal=True)
        disp = df_orders if sf == "全部" else df_orders[df_orders["目前狀態"] == sf]
        for idx, row in disp.iterrows():
            with st.expander(f"【{row['目前狀態']}】 單號:{row['訂單編號']} - {row['顧客姓名']}"):
                st.write(f"特徵/洗法: {row['花色備註']}/{row['洗法備註']} ｜ 金額: ${row['總金額']} ({row['付款方式']})")
                c1, c2, c3, c4 = st.columns(4)
                if c1.button("設為：待清洗", key=f"w_{row['訂單編號']}"):
                    df_orders.at[idx, "目前狀態"] = "待清洗"
                    df_orders.to_csv(O_FILE, index=False)
                    st.rerun()
                if c2.button("設為：清洗中", key=f"s_{row['訂單編號']}"):
                    df_orders.at[idx, "currently"] = "清洗中"
                    df_orders.at[idx, "目前狀態"] = "清洗中"
                    df_orders.to_csv(O_FILE, index=False)
                    st.rerun()
                if c3.button("設為：已完成", key=f"d_{row['訂單編號']}"):
                    df_orders.at[idx, "currently"] = "已完成（待取）"
                    df_orders.at[idx, "目前狀態"] = "已完成（待取）"
                    df_orders.to_csv(O_FILE, index=False)
                    st.rerun()
                if c4.button("顧客已取件", key=f"p_{row['訂單編號']}"):
                    df_orders.at[idx, "currently"] = "已取件"
                    df_orders.at[idx, "目前狀態"] = "已取件"
                    df_orders.to_csv(O_FILE, index=False)
                    st.rerun()

with t3:
    st.header("🔍 客戶明細資料查詢")
    s_phone = st.text_input("請輸入客戶手機查詢：").strip()
    if s_phone:
        nm, bal, disc = get_cust(s_phone)
        if nm:
            st.subheader(f"👤 會員：{nm} ｜ 餘額：${bal} 元 ｜ 折扣比率：{disc}%")
        h_df = df_orders[df_orders["手機號碼"] == str(s_phone)]
        if h_df.empty:
            st.info("無消費紀錄")
        else:
            st.dataframe(h_df[["日期", "訂單編號", "衣服項目", "數量", "總金額", "付款方式", "目前狀態"]].sort_values(by="日期", ascending=False), use_container_width=True, hide_index=True)

with t4:
    st.header("📊 門市營業報表統計")
    if df_orders.empty:
        st.info("暫無數據")
    else:
        df_orders["僅日期"] = df_orders["日期"].apply(lambda x: str(x).split(" ")[0] if " " in str(x) else str(x))
        rt = st.radio("報表類別", ["營業日報表", "月結報表"], horizontal=True)
        if rt == "營業日報表":
            t_date = st.date_input("選擇日期", datetime.date.today())
            day_df = df_orders[df_orders["僅日期"] == t_date.strftime("%Y-%m-%d")]
            if day_df.empty:
                st.warning("當日無營業紀錄")
            else:
                st.metric("當日收件單數", f"{len(day_df)} 單")
                st.dataframe(day_df[["訂單編號", "顧客姓名", "衣服項目", "數量", "總金額", "付款方式", "目前狀態"]], use_container_width=True, hide_index=True)
        else:
            t_m = st.text_input("輸入月份 (例如 2026-10)", datetime.date.today().strftime("%Y-%m")).strip()
            m_df = df_orders[df_orders["僅日期"].str.startswith(t_m)]
            if m_df.empty:
                st.warning("該月份無營業紀錄")
            else:
                st.metric("全月收件單數", f"{len(m_df)} 單")
                st.dataframe(m_df[["日期", "訂單編號", "顧客姓名", "總金額", "付款方式"]], use_container_width=True, hide_index=True)
