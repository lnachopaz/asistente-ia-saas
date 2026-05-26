# 🤖 Asistente IA SaaS

Chatbot con inteligencia artificial para negocios, desarrollado con **FastAPI**, **LangChain** y **Google Gemini**.

## ¿Qué hace?

Permite a cualquier negocio tener un asistente virtual que responde preguntas de sus clientes en base a un manual personalizado. El negocio sube su información (menú, precios, políticas, FAQs) y el bot responde automáticamente de forma contextual.

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend / API | FastAPI + Uvicorn |
| Inteligencia Artificial | LangChain + Google Gemini |
| Base de datos | Supabase (PostgreSQL) |
| Patrón de IA | RAG (Retrieval-Augmented Generation) |

## ¿Cómo funciona?

1. Se carga el manual del negocio (ej: `manual_pizzeria.txt`) con su información, precios y políticas.
2. El script `cargar_datos.py` procesa el texto y lo almacena en Supabase.
3. Cuando un cliente pregunta algo, el sistema recupera la información relevante y genera una respuesta precisa con Google Gemini.

## Instalación

```bash
git clone https://github.com/lnachopaz/asistente-ia-saas
cd asistente-ia-saas
pip install -r requirements.txt
```

Crear un archivo `.env`:

```env
GOOGLE_API_KEY=tu_clave_de_gemini
SUPABASE_URL=tu_url_de_supabase
SUPABASE_KEY=tu_clave_de_supabase
```

Cargar datos e iniciar servidor:

```bash
python cargar_datos.py
uvicorn src.main:app --reload
```

## Estructura

```
asistente-ia-saas/
├── src/                  # API principal
├── cargar_datos.py       # Carga el manual a Supabase
├── manual_pizzeria.txt   # Ejemplo de manual de negocio
├── requirements.txt      # Dependencias Python
└── .env                  # Variables de entorno (no incluido)
```

## Estado

🚧 En desarrollo activo

---
Desarrollado por [Luis Ignacio Paz](https://www.linkedin.com/in/luisignaciopaz-ing)
