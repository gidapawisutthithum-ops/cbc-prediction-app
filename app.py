import streamlit as st
import pandas as pd
import pickle

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="CBC Analysis & Family Planning", layout="wide")

# ฟังก์ชันโหลดโมเดล (ใช้แคชเพื่อประหยัดทรัพยากร)
@st.cache_resource
def load_model():
    try:
        # หมายเหตุ: หากไฟล์ .pkcls เป็น Orange model อาจต้องใช้ห้องสมุด Orange ในการโหลด
        # ในที่นี้จะลองโหลดผ่าน pickle แบบมาตรฐาน
        with open('rf_anemia_model.pkcls', 'rb') as f:
            model = pickle.load(f)
        return model
    except Exception as e:
        st.error(f"ไม่สามารถโหลดโมเดลได้: {e}")
        return None

model = load_model()

st.title("🔬 ระบบวิเคราะห์ผล CBC เบื้องต้นและวางแผนครอบครัว")
st.write("เครื่องมือช่วยวิเคราะห์ความเสี่ยงจากผลเลือด สำหรับบุคลากรทางการแพทย์และนักศึกษา")

# เมนูเลือกโหมด
mode = st.sidebar.radio("เลือกโหมดการใช้งาน", ["วิเคราะห์รายบุคคล", "วางแผนครอบครัว (คู่สมรส)"])

# รายชื่อ Feature ที่โมเดลต้องการ (อ้างอิงจากไฟล์ CSV ของคุณ)
features = ['WBC', 'LYMp', 'NEUTp', 'LYMn', 'NEUTn', 'RBC', 'HGB', 'HCT', 'MCV', 'MCH', 'MCHC', 'PLT', 'PDW', 'PCT']

def input_cbc_data(label_prefix=""):
    st.subheader(f"กรอกข้อมูล {label_prefix}")
    col1, col2, col3 = st.columns(3)
    data = {}
    with col1:
        data['Age'] = st.number_input(f"อายุ (ปี) {label_prefix}", min_value=0, max_value=120, value=25)
        data['Gender'] = st.selectbox(f"เพศ {label_prefix}", ["ชาย", "หญิง"])
        data['WBC'] = st.number_input(f"WBC (10^3/uL) {label_prefix}", value=7.0)
        data['RBC'] = st.number_input(f"RBC (10^6/uL) {label_prefix}", value=4.5)
        data['HGB'] = st.number_input(f"HGB (g/dL) {label_prefix}", value=13.0)
    with col2:
        data['HCT'] = st.number_input(f"HCT (%) {label_prefix}", value=40.0)
        data['MCV'] = st.number_input(f"MCV (fL) {label_prefix}", value=85.0)
        data['MCH'] = st.number_input(f"MCH (pg) {label_prefix}", value=28.0)
        data['MCHC'] = st.number_input(f"MCHC (g/dL) {label_prefix}", value=33.0)
        data['PLT'] = st.number_input(f"PLT (10^3/uL) {label_prefix}", value=250.0)
    with col3:
        data['LYMp'] = st.number_input(f"LYM% {label_prefix}", value=30.0)
        data['NEUTp'] = st.number_input(f"NEUT% {label_prefix}", value=60.0)
        data['LYMn'] = st.number_input(f"LYM# {label_prefix}", value=2.0)
        data['NEUTn'] = st.number_input(f"NEUT# {label_prefix}", value=4.5)
        data['PDW'] = st.number_input(f"PDW {label_prefix}", value=12.0)
        data['PCT'] = st.number_input(f"PCT {label_prefix}", value=0.2)
    return data

def get_recommendation(diagnosis, mcv):
    if "Iron deficiency" in diagnosis or mcv < 80:
        return "คำแนะนำ: รับประทานอาหารที่มีธาตุเหล็กสูง และวิตามินซี ควรปรึกษาแพทย์"
    elif "Thalassemia" in diagnosis:
        return "คำแนะนำ: ควรตรวจเพิ่มด้วย Hb typing และตรวจคัดกรองคู่สมรส"
    else:
        return "คำแนะนำ: ผลอยู่ในเกณฑ์ปกติหรือควรติดตามผลตามคำแนะนำของแพทย์"

if mode == "วิเคราะห์รายบุคคล":
    user_data = input_cbc_data()
    if st.button("วิเคราะห์ผล"):
        df = pd.DataFrame([user_data])[features]
        if model:
            prediction = model.predict(df)[0]
            prob = model.predict_proba(df).max() * 100
            st.success(f"ผลการวิเคราะห์เบื้องต้น: **{prediction}** (ความแม่นยำ {prob:.2f}%)")
            st.info(get_recommendation(prediction, user_data['MCV']))
        else:
            st.warning("ระบบใช้เกณฑ์ MCV เบื้องต้น: " + ("สงสัยภาวะโลหิตจาง" if user_data['MCV'] < 80 else "ปกติ"))

elif mode == "วางแผนครอบครัว (คู่สมรส)":
    c1, c2 = st.columns(2)
    with c1:
        p1 = input_cbc_data("ฝ่ายชาย")
    with c2:
        p2 = input_cbc_data("ฝ่ายหญิง")
    
    if st.button("ประเมินความเสี่ยงส่งต่อบุตร"):
        if p1['MCV'] < 80 and p2['MCV'] < 80:
            st.error("⚠️ ความเสี่ยงสูง: ทั้งคู่มีภาวะ MCV ต่ำ สงสัยพาหะธาลัสซีเมียคู่")
        elif p1['MCV'] < 80 or p2['MCV'] < 80:
            st.warning("⚠️ ความเสี่ยงปานกลาง: ฝ่ายใดฝ่ายหนึ่งมีภาวะ MCV ต่ำ")
        else:
            st.success("✅ ความเสี่ยงต่ำ: ทั้งคู่มีค่า MCV ในเกณฑ์ปกติ")
