import re
import streamlit as st
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import io
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
)

st.set_page_config(page_title="数学電卓", layout="wide")

st.title("📊 数学電卓 & グラフ描画")

# **数式と結果の状態管理**
if "expression" not in st.session_state:
    st.session_state.expression = ""
if "result" not in st.session_state:
    st.session_state.result = ""


# **数式の修正関数**
def format_expression(expression):
    expression = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expression)  # `2x` → `2*x`
    expression = re.sub(r'(\d)\(', r'\1*(', expression)  # `2(x+1)` → `2*(x+1)`
    expression = re.sub(r'\)([a-zA-Z])', r')*\1', expression)  # `)x` → `)*x`
    expression = re.sub(r'(?<!\w)(sin|cos|tan|log|sqrt|exp|sinh|cosh|tanh)(\d+)', r'\1(\2)', expression)  # `sin30` → `sin(30)`
    return expression


# ボタン押下時の処理
def update_expression(value):
    if value == "C":
        st.session_state.expression = ""
        st.session_state.result = ""
    elif value == "DEL":
        st.session_state.expression = st.session_state.expression[:-1]  # 1文字削除
    elif value == "=":
        if st.session_state.expression:
            try:
                formatted_expr = format_expression(st.session_state.expression)
                x = sp.Symbol('x')
                expr = formatted_expr.replace("^", "**").replace("log", "log10")

                try:
                    sympy_expr = sp.sympify(expr, evaluate=True)
                    result = sympy_expr.evalf() if sympy_expr.is_number else sympy_expr
                    st.session_state.result = result
                except sp.SympifyError:  # ✅ 数式の書式エラー
                    logging.warning(f"数式のエラー: {st.session_state.expression}")
                    st.session_state.result = "数式の書式が正しくありません。"
                except ValueError:  # ✅ 計算エラー
                    logging.warning(f"計算エラー: {st.session_state.expression}")
                    st.session_state.result = "計算エラー：入力を確認してください。"
                except Exception as e:  # ✅ その他のエラー
                    logging.error(f"未知のエラー: {e}")
                    st.session_state.result = "内部エラーが発生しました。"
            except Exception as e:
                logging.error(f"数式の処理中にエラー: {e}")
                st.session_state.result = "内部エラーが発生しました。"
    elif value == "π":
        st.session_state.expression += "pi"
    elif value == "e":
        st.session_state.expression += "E"
    else:
        st.session_state.expression += value


# UI: 数式表示
st.markdown(f"<h2 style='text-align: center; color: #2C3E50;'>{st.session_state.expression}</h2>", unsafe_allow_html=True)

# 計算結果の表示エリアを確保
result_placeholder = st.empty()
result_placeholder.markdown(f"<h1 style='text-align: center; color: #E74C3C;'>{st.session_state.result or '&nbsp;'}</h1>", unsafe_allow_html=True)

# ボタン配置
col1, col2, col3 = st.columns([1, 1, 1.5])

# 数字ボタン
with col1:
    st.subheader("数字")
    for row in [["7", "8", "9"], ["4", "5", "6"], ["1", "2", "3"], ["0", ".", "x"]]:
        cols = st.columns(len(row))
        for i, val in enumerate(row):
            cols[i].button(val, key=f"num_{val}", use_container_width=True, on_click=update_expression, args=(val,))

# 演算ボタン
with col2:
    st.subheader("演算")
    for row in [["+", "-", "*", "/"], ["(", ")", "^", "="], ["C", "DEL"]]:
        cols = st.columns(len(row))
        for i, val in enumerate(row):
            button_label = f"`{val}`"
            cols[i].button(button_label, key=f"op_{val}", use_container_width=True, on_click=update_expression, args=(val,))

# 関数ボタン
with col3:
    st.subheader("関数")
    for row in [["sin", "cos", "tan", "log"], ["asin", "acos", "atan", "sqrt"], ["sinh", "cosh", "tanh", "exp"], ["π", "e"]]:
        cols = st.columns(len(row))
        for i, val in enumerate(row):
            cols[i].button(val, key=f"fn_{val}", use_container_width=True, on_click=update_expression, args=(val,))

# x の範囲をスライダーで調整
st.subheader("📈 グラフ設定")
x_min, x_max = st.slider("x の範囲", -20.0, 20.0, (-10.0, 10.0), step=0.5)

# グラフ描画
if st.session_state.result and "x" in st.session_state.expression:
    try:
        formatted_expr = format_expression(st.session_state.expression)
        x = sp.Symbol('x')
        expr = formatted_expr.replace("^", "**").replace("log", "log10")
        expr = sp.sympify(expr, evaluate=True)

        f = sp.lambdify(x, expr, modules=["numpy",
            {"sin": lambda v: np.sin(np.radians(v)),
             "cos": lambda v: np.cos(np.radians(v)),
             "tan": lambda v: np.tan(np.radians(v)),
             "asin": lambda v: np.degrees(np.arcsin(v)),
             "acos": lambda v: np.degrees(np.arccos(v)),
             "atan": lambda v: np.degrees(np.arctan(v))}])

        x_vals = np.linspace(x_min, x_max, 400)
        y_vals = np.vectorize(f)(x_vals)

        fig, ax = plt.subplots()
        ax.plot(x_vals, y_vals, label=str(expr))
        ax.axhline(0, color='black', linewidth=0.5)
        ax.axvline(0, color='black', linewidth=0.5)
        ax.grid(True)
        ax.legend()

        # グラフの表示
        st.pyplot(fig)

        # 画像を保存してダウンロード
        img_bytes = io.BytesIO()
        fig.savefig(img_bytes, format="png")
        img_bytes.seek(0)

        st.download_button(
            label="📥 グラフをダウンロード",
            data=img_bytes,
            file_name="graph.png",
            mime="image/png"
        )

    except Exception as e:
        logging.error(f"グラフ描画エラー: {e}")
        st.error("グラフを描画できませんでした。")
