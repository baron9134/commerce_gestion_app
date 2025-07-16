import streamlit as st
import json
import os
import pandas as pd
import altair as alt

DATA_FILE = "stock.json"

# --------------- Utils ---------------
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def add_product(name, quantity, price, category):
    data = load_data()
    data.append({
        "name": name,
        "quantity": quantity,
        "price": price,
        "category": category
    })
    save_data(data)

def delete_product(index):
    data = load_data()
    if 0 <= index < len(data):
        del data[index]
        save_data(data)

def update_product(index, quantity=None, price=None):
    data = load_data()
    if quantity is not None:
        data[index]["quantity"] = quantity
    if price is not None:
        data[index]["price"] = price
    save_data(data)

# --------------- UI ---------------
st.set_page_config(page_title="Stock App", layout="wide")
st.title("📦 Gestion de Stock")

data = load_data()

# --------- SIDEBAR ---------
st.sidebar.markdown("### 📊 Affichage")
view_option = st.sidebar.radio("Choisir une vue :", ["📋 Articles", "📈 Graphique"])

st.sidebar.header("➕ Ajouter un produit")
name = st.sidebar.text_input("Nom du produit")
quantity = st.sidebar.number_input("Quantité", min_value=0, step=1)
price = st.sidebar.number_input("Prix unitaire (FC)", min_value=0, step=100)
category_choice = st.sidebar.selectbox("Catégorie", ["Alimentation", "Boisson", "Électronique", "Autre"])
category = st.sidebar.text_input("Catégorie personnalisée") if category_choice == "Autre" else category_choice

if st.sidebar.button("Ajouter"):
    if name:
        add_product(name, quantity, price, category)
        st.sidebar.success(f"Produit '{name}' ajouté.")
        st.experimental_rerun()
    else:
        st.sidebar.error("Le nom est requis.")

# --------- STATS ---------
total_articles = sum([p["quantity"] for p in data])
valeur_totale = sum([p["quantity"] * p["price"] for p in data])
alertes_stock_faible = sum([1 for p in data if p["quantity"] < 5])

col1, col2, col3 = st.columns(3)
col1.metric("Total articles en stock", total_articles)
col2.metric("Valeur totale (FC)", f"{valeur_totale:,}")
col3.metric("Produits en alerte ⚠️", alertes_stock_faible)

# --------- MAIN VIEW ---------
def render_products(filtered_data):
    cols = st.columns(3)
    for i, product in enumerate(filtered_data):
        with cols[i % 3]:
            st.markdown("----")
            st.markdown(f"### {product['name']}")
            st.write(f"Catégorie : {product.get('category', 'Non spécifiée')}")
            
            if product['quantity'] < 5:
                st.warning(f"⚠️ Stock faible : {product['quantity']} unités")
            else:
                st.write(f"Quantité : **{product['quantity']}**")
            
            st.write(f"Prix : {product['price']} FC")
            st.write(f"Valeur totale : {product['quantity'] * product['price']} FC")

            with st.expander("🛠 Modifier"):
                new_qty = st.number_input(
                    f"Nouvelle quantité - {product['name']}",
                    min_value=0,
                    step=1,
                    key=f"qty_{i}_{product['name']}"
                )
                new_price = st.number_input(
                    f"Nouveau prix - {product['name']}",
                    min_value=0,
                    step=100,
                    key=f"price_{i}_{product['name']}"
                )

                if st.button("Mettre à jour", key=f"update_{i}_{product['name']}"):
                    update_product(i, new_qty, new_price)
                    st.success("Mis à jour !")
                    st.experimental_rerun()

                if st.button("🗑 Supprimer", key=f"delete_{i}_{product['name']}"):
                    delete_product(i)
                    st.warning("Supprimé")
                    st.experimental_rerun()

if view_option == "📋 Articles":
    st.subheader("📋 Articles en stock")

    # Recherche par nom
    search_query = st.text_input("🔍 Rechercher un produit par nom")

    # Filtrer par stock faible
    show_low_stock_only = st.checkbox("⚠️ Afficher uniquement les produits en stock faible (<5)")

    col_search, col_button = st.columns([3, 1])
    with col_button:
        if st.button("Tout afficher"):
            search_query = ""
            show_low_stock_only = False

    # Filtrage
    filtered_data = []
    for product in data:
        name_match = search_query.lower() in product["name"].lower()
        low_stock_match = not show_low_stock_only or product["quantity"] < 5
        if name_match and low_stock_match:
            filtered_data.append(product)

    categories = sorted(list(set(p.get("category", "Non spécifiée") for p in data)))
    selected_category = st.selectbox("📂 Filtrer par catégorie", ["Toutes"] + categories)

    if selected_category != "Toutes":
        filtered_data = [p for p in filtered_data if p.get("category") == selected_category]

    render_products(filtered_data)

elif view_option == "📈 Graphique":
    st.subheader("📊 Répartition des quantités par produit")
    if data:
        df = pd.DataFrame(data)

        bar_chart = alt.Chart(df).mark_bar().encode(
            x=alt.X("name:N", title="Produit"),
            y=alt.Y("quantity:Q", title="Quantité"),
            tooltip=["name", "quantity"]
        ).properties(
            width=700,
            height=400
        ).configure_mark(
            color="steelblue"
        )

        st.altair_chart(bar_chart, use_container_width=True)
        
        st.subheader("💰 Valeur totale par produit")
        df["valeur_totale"] = df["quantity"] * df["price"]
        st.bar_chart(df.set_index("name")["valeur_totale"])
    else:
        st.info("Aucun produit à afficher.")

# --------- EXPORT ---------
st.markdown("----")
if st.button("📤 Exporter en CSV"):
    df = pd.DataFrame(data)
    df["valeur_totale"] = df["quantity"] * df["price"]
    df.to_csv("stock.csv", index=False)
    st.success("Fichier 'stock.csv' exporté avec succès ✅")

