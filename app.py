
import streamlit as st
import pandas as pd
import datetime
import os

st.set_page_config(page_title="洗衣店雲端管理系統", layout="wide")

# ==================== 🔐 安全密碼登入驗證 ====================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 歡迎使用洗衣店管理系統")
    st.subheader("本系統僅供店主與員工使用，請輸入管理密碼：")
    
    password = st.text_input("請輸入密碼：", type="password")
    login_btn = st.button("登入系統")
    
    # 預設密碼是 1234，你可以自行修改下方數字
    if login_btn:
        if password == "1234":  
            st.session_state.authenticated = True
            st.success("✅ 密碼正確，正在登入...")
            st.rerun()
        else:
            st.error("❌ 密碼錯誤，請重新輸入！")
    st.stop()

# ==================== 🔓 登入成功後的系統主體 ====================
ORDERS_FILE = "laundry_orders.csv"
CUSTOMERS_FILE = "laundry_customers.csv"

PRICE_LIST = {
    "一般襯衫/T恤": 50, "長褲/牛仔褲": 60, "厚外套/大衣": 150, "床單/被套": 200, "毛毯/特殊材質": 300
}

if os.path.exists(ORDERS_FILE):
    df_orders = pd.read_csv(ORDERS_FILE)
    df_orders["手機號碼"] = df_orders["手機號碼"].astype(str)
else:
    df_orders = pd.DataFrame(columns=["訂單編號", "日期", "顧客姓名", "手機號碼", "衣服項目", "數量", "總金額", "目前狀態", "付款方式"])

if os.path.exists(CUSTOMERS_FILE):
    df_cust = pd.read_csv(CUSTOMERS_FILE)
    df_cust["手機號碼"] = df_cust["手機號碼"].astype(str)
else:
    df_cust = pd.DataFrame(columns=["手機號碼", "顧客姓名", "儲值餘額"])

if "receipt_data" not in st.session_state:
    st.session_state.receipt_data = None

def get_customer_info(phone):
    match = df_cust[df_cust["手機號碼"] == str(phone)]
    if not match.empty:
        return match.iloc[0]["顧客姓名"], match.iloc[0]["儲值餘額"]
    return None, 0

tab1, tab2, tab3 = st.tabs(["📥 新單收件與儲值", "📋 當前狀態看板", "🔍 客戶歷史資料查詢"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.header("💰 會員儲值與開戶")
        with st.form("deposit_form"):
            c_phone = st.text_input("會員手機號碼", placeholder="請輸入10碼手機").strip()
            c_name = st.text_input("會員姓名", placeholder="新會員請輸入姓名")
            amount = st.number_input("儲值金額 (元)", min_value=0, value=0, step=100)
            deposit_btn = st.form_submit_button("執行儲值 / 開戶")
            
            if deposit_btn:
                if not c_phone:
                    st.error("❌ 請輸入手機號碼")
                else:
                    idx = df_cust[df_cust["手機號碼"] == c_phone].index
                    if len(idx) > 0:
                        df_cust.at[idx[0], "儲值餘額"] += amount
                        name_to_show = df_cust.at[idx[0], "顧客姓名"]
                        st.success(f"✅ 儲值成功！{name_to_show} 目前餘額：${df_cust.at[idx[0], '儲值餘額']} 元")
                    else:
                        if not c_name:
                            st.error("❌ 新客戶請填寫姓名以進行開戶")
                        else:
                            new_c = {"手機號碼": c_phone, "顧客姓名": c_name, "儲值餘額": amount}
                            df_cust = pd.concat([df_cust, pd.DataFrame([new_c])], ignore_index=True)
                            st.success(f"🎉 開戶成功！{c_name} 目前餘額：${amount} 元")
                    df_cust.to_csv(CUSTOMERS_FILE, index=False)
                    st.rerun()

    with col2:
        st.header("📥 新單收件登記")
        with st.form("order_form", clear_on_submit=True):
            o_phone = st.text_input("顧客手機號碼", placeholder="請輸入手機").strip()
            current_name, current_balance = get_customer_info(o_phone)
            if o_phone and current_name:
                st.caption(f"💡 找到會員：{current_name} ｜ 當前儲值餘額：${current_balance} 元")
            elif o_phone:
                st.caption("⚠️ 此手機非儲值會員，結帳時將以【現金】計算。")
                
            selected_item = st.selectbox("衣服種類", list(PRICE_LIST.keys()))
            quantity = st.number_input("數量", min_value=1, value=1, step=1)
            pay_method = st.radio("付款方式", ["儲值金扣款", "現金結帳"], horizontal=True)
            
            unit_price = PRICE_LIST[selected_item]
            total_price = unit_price * quantity
            st.info(f"💰 總金額: **${total_price}** 元")
            submit_btn = st.form_submit_button("確定收件")
            
            if submit_btn:
                if not o_phone:
                    st.error("❌ 請輸入手機號碼！")
                else:
                    can_order = True
                    cust_idx = df_cust[df_cust["手機號碼"] == o_phone].index
                    
                    if pay_method == "儲值金扣款":
                        if len(cust_idx) == 0:
                            st.error("❌ 該手機號碼不是儲值會員，請選擇現金或先前往左側開戶。")
                            can_order = False
                        elif df_cust.at[cust_idx[0], "儲值餘額"] < total_price:
                            st.error(f"❌ 餘額不足！當前餘額為 ${df_cust.at[cust_idx[0], '儲值餘額']}。")
                            can_order = False
                        else:
                            df_cust.at[cust_idx[0], "儲值餘額"] -= total_price
                            df_cust.to_csv(CUSTOMERS_FILE, index=False)
                    
                    if can_order:
                        final_name = df_cust.at[cust_idx[0], "顧客姓名"] if len(cust_idx) > 0 else "現場散客"
                        order_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                        today_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        _, updated_balance = get_customer_info(o_phone)
                        rem_bal_str = f"${updated_balance} 元" if len(cust_idx) > 0 else "不適用 (現金散客)"
                        
                        new_order = {
                            "訂單編號": order_id, "日期": today_str, "顧客姓名": final_name,
                            "手機號碼": o_phone, "衣服項目": selected_item, "數量": quantity,
                            "總金額": total_price, "目前狀態": "待清洗", "付款方式": pay_method
                        }
                        df_orders = pd.concat([df_orders, pd.DataFrame([new_order])], ignore_index=True)
                        df_orders.to_csv(ORDERS_FILE, index=False)
                        st.session_state.receipt_data = {
                            "id": order_id, "date": today_str, "name": final_name, "phone": o_phone,
                            "item": selected_item, "qty": quantity, "total": total_price,
                            "pay": pay_method, "balance": rem_bal_str
                        }
                        st.success(f"✅ 收件成功！已生成收據憑證。")
                        st.rerun()

    if st.session_state.receipt_data:
        st.write("---")
        st.header("🖨️ 剛才生成的收據憑證")
        r = st.session_state.receipt_data
        receipt_html = f"""
        <div style="background-color: #ffffff; color: #000000; padding: 20px; font-family: sans-serif; max-width: 350px; border: 1px solid #ccc; border-radius: 5px; margin-bottom: 10px;">
            <h3 style="text-align: center; margin: 0;">✨ 潔淨專業洗衣店 ✨</h3>
            <p style="text-align: center; font-size: 12px; margin: 5px 0;">～ 感謝您的光臨 ～</p>
            <p>--------------------------------</p>
            <p style="margin: 5px 0;"><b>收件日期:</b> {r['date']}</p>
            <p style="margin: 5px 0;"><b>單號:</b> {r['id']}</p>
            <p style="margin: 5px 0;"><b>客戶:</b> {r['name']}</p>
            <p style="margin: 5px 0;"><b>電話:</b> {r['phone']}</p>
            <p>--------------------------------</p>
            <p style="margin: 5px 0;"><b>品項:</b> {r['item']}</p>
            <p style="margin: 5px 0;"><b>數量:</b> {r['qty']} 件</p>
            <p style="margin: 5px 0;"><b>本次消費:</b> ${r['total']} 元</p>
            <p style="margin: 5px 0;"><b>付款方式:</b> {r['pay']}</p>
            <p>--------------------------------</p>
            <p style="margin: 5px 0; font-size: 16px;"><b>💰 帳戶剩餘餘額: {r['balance']}</b></p>
            <p>--------------------------------</p>
            <p style="font-size: 11px; text-align: center; margin: 5px 0;">※ 請憑此單取件 ※</p>
        </div>
        """
        st.markdown(receipt_html, unsafe_allow_html=True)
        if st.button("關閉收據顯示 / 收件下一位"):
            st.session_state.receipt_data = None
            st.rerun()

with tab2:
    st.header("📋 當前衣物清洗進度")
    if df_orders.empty:
        st.info("目前沒有任何訂單。")
    else:
        status_filter = st.radio("篩選進度：", ["全部", "待清洗", "清洗中", "已完成（待取）", "已取件"], horizontal=True)
        display_df = df_orders if status_filter == "全部" else df_orders[df_orders["目前狀態"] == status_filter]
        
        for index, row in display_df.iterrows():
            status = row["目前狀態"]
            color = "🔴" if status == "待清洗" else "🟡" if status == "清洗中" else "🟢" if status == "已完成（待取）" else "⚪"
            with st.expander(f"{color} 【{status}】 單號:{row['訂單編號']} - {row['顧客姓名']}"):
                st.write(f"電話：{row['手機號碼']} ｜ 金額：${row['總金額']} ({row['付款方式']})")
                cc1, cc2, cc3, cc4 = st.columns(4)
                if cc1.button("設為：待清洗", key=f"w_{row['訂單編號']}"):
                    df_orders.at[index, "目前狀態"] = "待清洗"
                    df_orders.to_csv(ORDERS_FILE, index=False)
                    st.rerun()
                if cc2.button("設為：清洗中", key=f"s_{row['訂單編號']}"):
                    df_orders.at[index, "目前狀態"] = "清洗中"
                    df_orders.to_csv(ORDERS_FILE, index=False)
                    st.rerun()
                if cc3.button("設為：已完成", key=f"d_{row['訂單編號']}"):
                    df_orders.at[index, "目前狀態"] = "已完成（待取）"
                    df_orders.to_csv(ORDERS_FILE, index=False)
                    st.rerun()
                if cc4.button("顧客已取件", key=f"p_{row['訂單編號']}"):
                    df_orders.at[index, "currently"] = "已取件"
                    df_orders.at[index, "目前狀態"] = "已取件"
                    df_orders.to_csv(ORDERS_FILE, index=False)
                    st.rerun()

with tab3:
    st.header("🔍 客戶歷史檔案與對帳查詢")
    search_phone = st.text_input("輸入客戶手機號碼進行查詢：", key="search_bar").strip()
    if search_phone:
        c_name_match, c_bal_match = get_customer_info(search_phone)
        if c_name_match:
            st.subheader(f"👤 會員：{c_name_match}")

