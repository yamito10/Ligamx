import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def hello_world():
    name = os.environ.get("NAME", "World")
    return f"Hello {name}!"

@app.route("/api/news", methods=['GET'])
def get_news():
    url = "https://www.record.com.mx/futbol/liga-mx"
    news_list = []
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Busca todos los enlaces que contengan '/futbol/' en el href
        article_links = soup.find_all('a', href=lambda x: x and '/futbol/' in x)
        for i, link_tag in enumerate(article_links[:10]):  # Limita a 10 noticias
            # Extrae el título (texto dentro de la etiqueta <a>)
            title = link_tag.get_text(strip=True) if link_tag else "Título no encontrado"

            # Extrae el enlace
            link = link_tag['href'] if link_tag and link_tag.get('href') else "#"
            if link and not link.startswith('http'):
                link = "https://www.record.com.mx" + link

            # Extrae el resumen (texto siguiente al enlace, si existe)
            summary = "Resumen no disponible"
            next_sibling = link_tag.find_next_sibling(string=True)
            if not next_sibling:
                next_sibling = link_tag.parent.find_next_sibling(string=True)
            if next_sibling:
                summary = next_sibling.strip()[:200]  # Limita el resumen a 200 caracteres

            # Intenta encontrar la imagen real
image_tag = link_tag.find_previous('img') # Busca la etiqueta <img> más cercana antes del enlace
if not image_tag:
    # Si no la encuentra, busca dentro del elemento "padre" del enlace
    image_tag = link_tag.find_parent().find('img')

if image_tag and image_tag.get('src'):
    image = image_tag['src']
    # A veces las URLs de las imágenes son relativas, hay que completarlas
    if not image.startswith('http'):
        image = "https://www.record.com.mx" + image
else:
    # Si no encuentra ninguna imagen, usa el placeholder
    image = "https://placehold.co/600x400/e2e8f0/4a5568?text=Imagen+no+disponible"

            # Extrae la categoría (por ejemplo, 'América', 'Cruz Azul')
            category = "Desconocida"
            parent = link_tag.parent
            category_tag = parent.find_previous(string=True, text=lambda x: x and x.strip() in ['América', 'Cruz Azul', 'Tigres', 'Pumas', 'Mazatlán FC', 'Necaxa', 'LIGA MX', 'Atlas', 'Tijuana', 'Juárez FC', 'Futbol de Estufa'])
            if category_tag:
                category = category_tag.strip()

            # Extrae la fecha (por ejemplo, '12/07/2025 - 12:38')
            date = "Fecha no encontrada"
            date_tag = parent.find_previous(string=True, text=lambda x: x and x.strip().startswith('|') and '-' in x)
            if date_tag:
                date = date_tag.strip().lstrip('|').strip()

            news_list.append({
                "id": i + 1,
                "title": title,
                "summary": summary,
                "link": link,
                "image": image,
                "category": category,
                "date": date
            })

        if not news_list:
            return jsonify({"error": "No se encontraron noticias"}), 404

        return jsonify(news_list)

    except requests.exceptions.RequestException as e:
        print(f"Error al obtener la página: {e}")
        return jsonify({"error": "Error al cargar las noticias de la fuente externa"}), 500
    except Exception as e:
        print(f"Error inesperado: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))