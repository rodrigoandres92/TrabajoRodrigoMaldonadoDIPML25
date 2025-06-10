
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from textwrap import dedent
import os

# --- Configuración del Panel ---
st.set_page_config(layout="wide", page_title="Análisis de Ventas y Clientes")

# --- Paleta de Colores Pasteles ---
PASTEL_COLORS = [
    "#A1C9F4", "#FFB482", "#8DE5A1", "#FF9F9B", "#D0BBFF",
    "#DEBB9B", "#FAB0E4", "#CFCFCF", "#FFD6A5", "#BDE0FE"
]
sns.set_palette(PASTEL_COLORS)
px.defaults.color_continuous_scale = px.colors.sequential.Blues
px.defaults.color_discrete_sequence = PASTEL_COLORS

# --- Carga y Preparación de Datos ---
@st.cache_data
def load_data(file_path):
    """
    Carga, limpia y prepara los datos desde el archivo CSV.
    """
    try:
        df = pd.read_csv(file_path)

        # Estandarización de nombres de columnas
        df.columns = [col.strip().lower().replace(' ', '').replace('%', 'percent') for col in df.columns]

        # Conversión de tipos de datos
        df['date'] = pd.to_datetime(df['date'], format='%m/%d/%Y', errors='coerce')
        df['time'] = pd.to_datetime(df['time'], format='%H:%M', errors='coerce').dt.time

        # Extraer características de fecha y hora
        df['month'] = df['date'].dt.to_period('M').astype(str)
        df['dayofweek'] = df['date'].dt.day_name()
        df['hour'] = df['date'].dt.hour

        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        df['dayofweek'] = pd.Categorical(df['dayofweek'], categories=day_order, ordered=True)

        numeric_cols = ['unitprice', 'quantity', 'tax5percent', 'total', 'cogs', 'grossmarginpercentage', 'grossincome', 'rating']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        if df.isnull().sum().any():
            for col in df.select_dtypes(include=np.number).columns:
                df[col].fillna(df[col].median(), inplace=True)

        return df

    except FileNotFoundError:
        st.error(f"Error `FileNotFoundError`: No se encontró el archivo en la ruta esperada: '{file_path}'.")
        st.info("Por favor, verifica que el nombre del archivo ('data.csv') sea correcto y que esté en la misma carpeta que el script de la aplicación.")
        return None
    except Exception as e:
        st.exception(e)
        return None

# Construcción de ruta de archivo robusta
script_dir = os.path.dirname(os.path.abspath(__file__))
data_file_path = os.path.join(script_dir, "data.csv")

# Carga de los datos
data = load_data(data_file_path)

if data is not None:
    st.title("📊 Panel de Análisis de Ventas y Clientes")
    st.markdown("Análisis interactivo para mejorar la estrategia de marketing de una cadena de tiendas de conveniencia. Por Rodrigo Maldonado.")
    st.markdown("---")

    # --- Barra Lateral de Filtros ---
    st.sidebar.header("🎨 Filtros del Panel")

    cities = sorted(data['city'].unique())
    selected_city = st.sidebar.selectbox("Seleccionar Ciudad", options=["Todas"] + cities)
    if selected_city != "Todas":
        filtered_data = data[data['city'] == selected_city]
    else:
        filtered_data = data.copy()

    product_lines = sorted(filtered_data['productline'].unique())
    selected_lines = st.sidebar.multiselect("Filtrar por Línea de Producto", options=product_lines, default=product_lines)

    if selected_lines:
        filtered_data = filtered_data[filtered_data['productline'].isin(selected_lines)]
    else:
        st.sidebar.warning("Selecciona al menos una línea de producto.")
        filtered_data = pd.DataFrame() 

    # --- Cuerpo del Dashboard ---

    # 1. Selección de Variables Clave
    with st.expander("1. Selección de Variables Clave", expanded=True):
        st.markdown(dedent("""
            ### Variables Relevantes para el Análisis
            Para entender las ventas y el comportamiento de los clientes, seleccioné las siguientes variables del dataset (con nombres estandarizados a minúsculas):

            - **Variables Transaccionales:** `total`, `quantity`, `unitprice`, `date`, `time`.
              - **Importancia:** Son el núcleo del análisis de rendimiento. Nos dicen **cuánto** (`total`) y **cuándo** (`date`, `time`) compran los clientes. `quantity` y `unitprice` nos ayudan a entender la composición de esa venta.

            - **Variables de Producto:** `productline`.
              - **Importancia:** Esencial para entender qué categorías de productos son las más populares y rentables. Permite responder: ¿Debemos promocionar más "Food and beverages"? ¿Hay un bajo rendimiento en "Fashion accessories"?

            - **Variables de Cliente:** `customertype`, `gender`, `rating`.
              - **Importancia:** Permiten segmentar a los clientes y analizar sus patrones de compra y niveles de satisfacción. Esto es clave para personalizar el marketing. Por ejemplo, ¿los "Members" gastan más? ¿Están más satisfechos?

            - **Variables de Ubicación:** `city`, `branch`.
              - **Importancia:** Fundamentales para comparar el rendimiento entre diferentes sucursales y mercados geográficos. Permiten identificar tiendas con mejor desempeño para replicar sus estrategias o tiendas con problemas para intervenir.
        """))

    if not filtered_data.empty:
        # 2. Visualización Básica de Datos
        st.markdown("---")
        st.header("2. Visualización Básica de Datos")
        st.markdown("Exploración inicial para entender la distribución y relaciones de las variables clave.")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Tendencia de Ventas Totales")
            sales_over_time = filtered_data.groupby('month')['total'].sum()
            fig_line, ax_line = plt.subplots(figsize=(8, 4))
            sales_over_time.plot(kind='line', ax=ax_line, marker='o', color=PASTEL_COLORS[0])
            ax_line.set_title("Ventas Mensuales", fontsize=14)
            ax_line.set_xlabel("Mes")
            ax_line.set_ylabel("Ventas Totales")
            plt.xticks(rotation=45)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            st.pyplot(fig_line)
            st.markdown(dedent("""
            **Observación:** Este **gráfico de líneas** revela los patrones de ventas a lo largo de los meses disponibles en el dataset (3 meses). Es una herramienta fundamental para detectar **estacionalidad** aunque en un período muy breve en este caso (¿hay meses consistentemente más altos o bajos?), **tendencias** (¿están las ventas creciendo o decreciendo con el tiempo?) y el impacto de posibles campañas de marketing pasadas.
            """))

        with col2:
            st.subheader("Distribución del Gasto por Transacción")
            fig_hist, ax_hist = plt.subplots(figsize=(8, 4))
            sns.histplot(filtered_data['total'], kde=True, ax=ax_hist, color=PASTEL_COLORS[1])
            ax_hist.set_title("Frecuencia de Montos de Venta", fontsize=14)
            ax_hist.set_xlabel("Monto Total de Venta")
            ax_hist.set_ylabel("Frecuencia")
            st.pyplot(fig_hist)
            st.markdown(dedent("""
            **Observación:** El **histograma** muestra la distribución de los montos totales de cada venta. Nos permite observar en qué rango de precios se concentra la mayoría de las transacciones. Esto es crucial para entender el "segmento de mejores ventas" y si la estrategia debe enfocarse en aumentar el número de ventas pequeñas o en incentivar compras de mayor valor.
            """))

        # 3. Gráficos Compuestos y Contextualización
        st.markdown("---")
        st.header("3. Gráficos Compuestos y Contextualización")
        st.markdown("Combinamos variables para obtener una comprensión más profunda del negocio.")

        col3, col4 = st.columns(2)

        with col3:
            st.subheader("Ventas por Línea de Producto y Tipo de Cliente")
            fig_bar, ax_bar = plt.subplots(figsize=(8, 5))
            sns.barplot(data=filtered_data, x="total", y="productline", hue="customertype", estimator=sum, orient='h', ax=ax_bar, errorbar=None)
            ax_bar.set_title("Ventas por Línea de Producto y Tipo de Cliente", fontsize=14)
            ax_bar.set_xlabel("Ventas Totales Acumuladas")
            ax_bar.set_ylabel("")
            plt.tight_layout()
            st.pyplot(fig_bar)
            st.markdown(dedent("""
            **Comprensión Profunda:** Este **gráfico de barras agrupado** va más allá de solo mostrar qué producto vende más. Desglosa las ventas por tipo de cliente (`Member` vs. `Normal`), revelando qué segmentos de clientes prefieren qué líneas de producto. 

            **Argumento de Elección:** Elegí esta visualización porque compara de forma clara y directa una métrica (`total`) a través de dos dimensiones categóricas (`productline` y `customertype`). Es superior a dos gráficos separados, ya que permite una comparación visual inmediata del comportamiento de miembros y no miembros dentro de cada categoría.
            """))

        with col4:
            st.subheader("Rating Promedio por Sucursal y Género")
            rating_pivot = filtered_data.pivot_table(index='branch', columns='gender', values='rating', aggfunc='mean')
            fig_heatmap, ax_heatmap = plt.subplots(figsize=(8, 5))
            sns.heatmap(rating_pivot, annot=True, fmt=".1f", cmap=sns.light_palette(PASTEL_COLORS[2], as_cmap=True), linewidths=.5, ax=ax_heatmap)
            ax_heatmap.set_title("Rating Promedio por Sucursal y Género", fontsize=14)
            ax_heatmap.set_xlabel("Género")
            ax_heatmap.set_ylabel("Sucursal")
            st.pyplot(fig_heatmap)
            st.markdown(dedent("""
            **Comprensión Profunda:** El **mapa de calor** cruza la satisfacción del cliente (`rating`) con la ubicación (`branch`) y un segmento demográfico (`gender`). Permite identificar con un simple vistazo de color si existen "puntos fríos" (bajo rating) o "puntos calientes" (alto rating) en combinaciones específicas.

            **Argumento de Elección:** Esta técnica es extremadamente eficiente para representar una tercera dimensión (el rating, mediante color) sobre una matriz de dos variables categóricas. Es mucho más rápido de interpretar que una tabla de números o múltiples gráficos de barras.
            """))

        # 4. Visualización de Datos Multivariados
        st.markdown("---")
        st.header("4. Visualización de Datos Multivariados")
        st.markdown("Técnicas avanzadas para visualizar múltiples dimensiones simultáneamente.")

        st.subheader("Relaciones entre Métricas Numéricas (Pair Plot)")
        pairplot_vars = ['unitprice', 'quantity', 'total', 'rating']
        pairplot_sample = filtered_data[pairplot_vars + ['productline']].dropna().sample(n=min(500, len(filtered_data)))

        fig_pair = sns.pairplot(pairplot_sample, hue='productline', vars=pairplot_vars, palette=PASTEL_COLORS, corner=True)
        st.pyplot(fig_pair)
        st.markdown(dedent("""
        **Justificación y observación:** El **pair plot** es una técnica avanzada ideal para la fase exploratoria de un análisis multivariado. Muestra simultáneamente dos tipos de gráficos:
        1.  **Histogramas/KDE (en la diagonal):** Muestran la distribución de cada variable individual.
        2.  **Gráficos de Dispersión (fuera de la diagonal):** Muestran la relación entre cada par de variables.

        Se justifica su uso porque **facilita la interpretación de patrones complejos** al condensar una gran cantidad de información en una sola figura. Permite detectar rápidamente correlaciones (la clara relación lineal entre `quantity` y `total`), posibles agrupaciones (clusters) por `productline` y la presencia de outliers sin necesidad de crear docenas de gráficos individuales.
        """))

        # 5. Visualización en 3D
        st.markdown("---")
        st.header("5. Visualización en 3D")
        st.markdown("Añadiendo una dimensión extra para descubrir nuevos insights.")

        st.subheader("Relación 3D: Precio, Cantidad y Venta Total")
        plot_3d_sample = filtered_data.sample(n=min(1000, len(filtered_data)))
        fig_3d = px.scatter_3d(
            plot_3d_sample,
            x='unitprice',
            y='quantity',
            z='total',
            color='productline',
            opacity=0.7,
            title="Precio Unitario vs. Cantidad vs. Venta Total"
        )
        fig_3d.update_layout(margin=dict(l=0, r=0, b=0, t=40))
        st.plotly_chart(fig_3d, use_container_width=True)
        st.markdown(dedent("""
        **Discusión de la Visualización 3D:**
        - **Variables Elegidas:** Se eligió la relación entre `unitprice`, `quantity` y `total`.
        - **Por qué 3D es apropiado:** Estas tres variables están intrínsecamente conectadas (el total de la venta es una función del precio y la cantidad). Mientras que un gráfico 2D solo puede mostrar `precio vs. total` o `cantidad vs. total`, una visualización 3D nos permite observar la **superficie de la relación completa** de una sola vez.
        - **Insights Revelados:** Este gráfico puede revelar estrategias de negocio por línea de producto. Por ejemplo, podríamos observar un cluster de productos de "bajo precio, alta cantidad" (como "Food and beverages") en una zona del gráfico, mientras que "Electronic accessories" podría ocupar una zona de "alto precio, baja cantidad". Esto ayuda a visualizar el modelo de negocio de cada categoría, algo que no es tan evidente en 2D.
        """))

        # 6. Integración en un Dashboard
        st.markdown("---")
        with st.expander("6. Reflexión sobre la Integración en un Dashboard"):
            st.markdown(dedent("""
                ### Valor de un Dashboard Interactivo
                La integración de estas visualizaciones en un dashboard interactivo con Streamlit transforma un análisis estático en una herramienta dinámica de toma de decisiones:

                - **Intuitivo y Organizado:** El dashboard presenta los hallazgos de forma lógica y estructurada. Los filtros en la barra lateral permiten que incluso usuarios no técnicos puedan explorar los datos fácilmente.

                - **Mejora la Experiencia del Usuario:** En lugar de solicitar múltiples informes, los gerentes de marketing y operaciones pueden responder sus propias preguntas en tiempo real. Pueden, por ejemplo, aislar una ciudad, ver qué línea de producto es la más vendida y por qué tipo de cliente, todo en cuestión de segundos.

                - **Facilita la Toma de Decisiones:** La interactividad permite probar hipótesis sobre la marcha. Un gerente puede filtrar por una sucursal de bajo rendimiento, analizar sus patrones de venta y satisfacción, y compararlos con una sucursal de alto rendimiento para identificar áreas de mejora. Esto acelera el ciclo de "insight-a-acción", permitiendo a la empresa reaccionar más rápido a las oportunidades y desafíos del mercado.
            """))
    else:
        st.error("No hay datos disponibles para los filtros seleccionados. Por favor, amplía tu selección en la barra lateral.")
else:
    st.error("El dashboard no pudo inicializarse porque la carga de datos falló. Revisa los mensajes de depuración en la parte superior de la página.")

