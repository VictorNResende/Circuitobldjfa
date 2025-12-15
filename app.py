

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from concurrent.futures import ThreadPoolExecutor
import socket
import hashlib
import os

# ================== CONFIGURAÇÕES ==================
TIMEOUT_TCP = 2
MAX_THREADS = 20
PORTA_TESTE = 443  # pode mudar para 80 se quiser
ARQUIVO_PADRAO = "bld_jfa.xlsx"  # Excel que fica no GitHub

# ================== USUÁRIOS ==================
# ⚠️ Login simples (ideal para MVP / uso gratuito)
USUARIOS = {
    "admin": hashlib.sha256("admin123".encode()).hexdigest(),
    "usuario": hashlib.sha256("usuario123".encode()).hexdigest()
}

# ================== FUNÇÕES ==================

def autenticar(usuario, senha):
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    return usuario in USUARIOS and USUARIOS[usuario] == senha_hash


def testar_conectividade(ip, porta=PORTA_TESTE, timeout=TIMEOUT_TCP):
    try:
        sock = socket.create_connection((ip, porta), timeout=timeout)
        sock.close()
        return "UP"
    except socket.timeout:
        return "TIMEOUT"
    except ConnectionRefusedError:
        return "UP"  # host respondeu
    except Exception:
        return "DOWN"


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

if "logado" not in st.session_state:
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
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

# ================== SISTEMA ==================

else:
    st.title("🌐 Mapa de Monitoramento de Rede")

    st.markdown("### 📂 Fonte dos dados")

    # ================== LEITURA DA PLANILHA PADRÃO ==================

if os.path.exists(ARQUIVO_PADRAO):
    df = pd.read_excel(ARQUIVO_PADRAO)
    st.info("Planilha padrão carregada")
else:
    st.error("Arquivo dados.xlsx não encontrado no repositório")
    st.stop()

    df = df.dropna(subset=['LATITUDE', 'LONGITUDE', 'IP'])

    iniciar = st.button("▶️ START - Executar Monitoramento")

if iniciar:
    with st.spinner("Executando testes de conectividade..."):
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            resultados = list(executor.map(testar_conectividade, df['IP']))

    mapa = folium.Map(
        location=[df['LATITUDE'].mean(), df['LONGITUDE'].mean()],
        zoom_start=12
    )

    for (_, linha), status in zip(df.iterrows(), resultados):
        if status == "UP":
            cor = "green"
        elif status == "TIMEOUT":
            cor = "orange"
        else:
            cor = "red"

        folium.Marker(
            [linha['LATITUDE'], linha['LONGITUDE']],
            tooltip=linha['CLIENTE'],
            popup=criar_popup(linha),
            icon=folium.Icon(color=cor)
        ).add_to(mapa)

        if status != "UP":
            folium.CircleMarker(
                [linha['LATITUDE'], linha['LONGITUDE']],
                radius=20,
                color='#cc3134',
                fill=True,
                fill_color='#cc3134',
                fill_opacity=0.6
            ).add_to(mapa)

    st.session_state.mapa = mapa

if 'mapa' in st.session_state:
    st_folium(st.session_state.mapa, width=1200, height=650)

    if st.button("🚪 Logout"):
        st.session_state.logado = False
        st.rerun()

# ================== RODAPÉ ==================
st.markdown("---")
st.markdown("Sistema de Monitoramento de Rede • Streamlit Cloud • Gratuito")
