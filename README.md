### ✅ `README.md`:

````markdown
# Warehouse Management System (WMS) MVP – Django-Based

This project is a fully functional Minimum Viable Product (MVP) for a Warehouse Management System (WMS). It is designed to handle product data mapping, multi-format sales data ingestion, processing, visualization, and a lightweight AI-assisted query interface—all in a single Django-based backend.

---

## 🚀 Features

- **Multi-format Sales Data Upload**
  - Supports up to 5 different sales data formats.
  - Automatic detection and standardization of schema

- **SKU–MSKU Master Mapping**
  - Allows for mapping sales product codes (SKU) to master product codes (MSKU)
  - Unified mapping loader and interface

- **Sales Data Processing**
  - Cleans and validates uploaded files
  - Computes total units sold, total sales, average price, etc.

- **Dashboard & Analytics**
  - Visual dashboards (bar charts, line graphs, tables)
  - Built using Chart.js for dynamic and responsive charts

- **AI Query Interface (Pluggable)**
  - Placeholder implemented for AI-based query answering
  - Can be integrated with Gemma.cpp or similar models

- **User Upload Tracking**
  - Upload history with date, user, and record count
  - Admin view for auditing and logs

---

## 🧱 Tech Stack

- **Backend**: Django 5.x (Python 3.10+)
- **Database**: SQLite (default), pluggable with PostgreSQL
- **Frontend**: HTML5 + Bootstrap + Chart.js
- **AI Layer (optional)**: Gemma C++ small model (planned integration)

---

## 🛠️ Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/yourusername/wms-django.git
   cd wms-django
````

2. **Create virtual environment**

   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**

   ```bash
   python manage.py migrate
   ```

5. **Run the server**

   ```bash
   python manage.py runserver
   ```

6. **Access the app**

   ```
   http://127.0.0.1:8000/
   ```

---

## 📁 Project Structure

```
wms_project/
├── wms_app/
│   ├── templates/
│   │   ├── upload.html
│   │   ├── dashboard.html
│   │   └── ai_query.html
│   ├── static/
│   │   └── js/
│   │       └── chart-render.js
│   ├── views.py
│   ├── models.py
│   ├── forms.py
│   ├── utils/
│   │   └── format_processor.py
│   └── ...
├── media/
├── db.sqlite3
├── manage.py
└── README.md
```

---

## 📌 Usage

1. **Upload Sales Data**

   * Go to `/` (Home)
   * Choose file and select type
   * Click upload

2. **View Dashboard**

   * Go to `/dashboard/` to visualize sales performance

3. **Run AI Queries**

   * Visit `/ai/` and enter a natural language question (e.g., "Show total sales for April")

---

## 🧩 Customization

* To support more file types:
  Add logic to `utils/format_processor.py`

* To enable AI integration:
  Plug in your model endpoint in `views.py → ai_query_view()`

---

## 🔐 Authentication

Basic login system can be extended with Django’s built-in authentication or social logins via `django-allauth`.

---

