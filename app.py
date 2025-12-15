
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import subprocess
import platform
from concurrent.futures import ThreadPoolExecutor
import hashlib

# ================== CONFIGURAÇÕES ==================
TIMEOUT_PING = 2
MAX_THREADS = 20

# ================== USUÁRIOS (SIMPLES / GRATUITO) ==================
# ⚠️ Ideal para MVP / uso público controlado
USUARIOS = {
    "admin": hashlib.sha256("admin123".encode()).hexdigest(),
    "usuario": hashlib.sha256("usuario123".encode()).hexdigest()
}

# ================== FUNÇÕES ==================

def autenticar(usuario, senha):
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    return usuario in USUARIOS and USUARIOS[usuario] == senha_hash


def ping_ip(ip):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    comando = ['ping', param, '1', ip]
    try:
        resultado = subprocess.run(
            comando,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=TIMEOUT_PING
        )
        return resultado.returncode == 0
    except subprocess.TimeoutExpired:
        return False


def criar_popup(linha):
    return folium.Popup(
        f"""
        <b>Cliente:</b> {linha['CLIENTE']}<br>
        <b>IP:</b> {linha['IP']}<br>
        <b>DSG:</b> {linha['DSG']}<br>
        <b>Sigla:</b> {linha['SIGLA']}<br>
        <b>Tecnologia:</b> {linha['TEC']}<br>
        <b>Serviço:</b> {linha['SERVIÇO']}
        """,
        max_width=300
    )

# ================== INTERFACE ==================

st.set_page_config(page_title="Mapa de Rede", layout="wide")

if 'logado' not in st.session_state:
    st.session_state.logado = False

# ================== LOGIN ==================

if not st.session_state.logado:
    st.title("🔐 Acesso ao Sistema")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if autenticar(usuario, senha):
            st.session_state.logado = True
            st.success("Login realizado com sucesso")
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos")

# ================== SISTEMA ==================

else:
    st.title("🌐 Mapa de Monitoramento de Rede")

    arquivo = st.file_uploader("📂 Envie a planilha Excel", type=['xlsx'])

    iniciar = st.button("▶️ START - Executar Monitoramento")

    if iniciar and arquivo:
        df = pd.read_excel(arquivo)
        df = df.dropna(subset=['LATITUDE', 'LONGITUDE', 'IP'])

        with st.spinner("Executando testes de conectividade..."):
            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                resultados = list(executor.map(ping_ip, df['IP']))

        mapa = folium.Map(
            location=[df['LATITUDE'].mean(), df['LONGITUDE'].mean()],
            zoom_start=12
        )

        for (_, linha), status in zip(df.iterrows(), resultados):
            cor = 'green' if status else 'red'

            folium.Marker(
                [linha['LATITUDE'], linha['LONGITUDE']],
                tooltip=linha['CLIENTE'],
                popup=criar_popup(linha),
                icon=folium.Icon(color=cor)
            ).add_to(mapa)

            if not status:
                folium.CircleMarker(
                    [linha['LATITUDE'], linha['LONGITUDE']],
                    radius=20,
                    color='#cc3134',
                    fill=True,
                    fill_color='#cc3134',
                    fill_opacity=0.6
                ).add_to(mapa)

        st_folium(mapa, width=1200, height=650)

    elif iniciar and not arquivo:
        st.warning("Envie uma planilha antes de iniciar")

    if st.button("🚪 Logout"):
        st.session_state.logado = False
        st.experimental_rerun()

# ================== RODAPÉ ==================
st.markdown("---")
st.markdown("Sistema de Monitoramento de Rede • Streamlit • Gratuito")
