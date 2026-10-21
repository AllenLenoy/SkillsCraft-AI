<div align="center">

# 🏺 SkillsCraft AI (CraftConnect)
### *AI-Empowered Fair-Trade Handcrafted Commerce & Heritage Journal*

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.1-092E20?logo=django&logoColor=white)](https://djangoproject.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-336791?logo=postgresql&logoColor=white)](https://supabase.com)
[![AI Provider](https://img.shields.io/badge/AI-OpenRouter%20%7C%20Nemotron-purple?logo=openai&logoColor=white)](https://openrouter.ai)
[![Tests](https://img.shields.io/badge/Tests-40%20Passed-brightgreen?logo=pytest&logoColor=white)](#-testing--quality-assurance)
[![License](https://img.shields.io/badge/License-MIT-amber.svg)](LICENSE)

*Connecting generational Indian master artisans directly with conscious global patrons through slow-craft storytelling, open-source AI listing assistants, and direct 88% studio remittances.*

---

</div>

## 📖 Table of Contents
- [✨ Project Overview](#-project-overview)
- [🌟 Key Innovations & Features](#-key-innovations--features)
- [🏛️ System Architecture](#️-system-architecture)
- [🛠️ Tech Stack](#️-tech-stack)
- [🚀 Quickstart & Installation](#-quickstart--installation)
- [⚡ Supabase PostgreSQL Setup](#-supabase-postgresql-setup)
- [🤖 Open-Source AI Service Integration](#-open-source-ai-service-integration)
- [👥 Pre-configured Demo Accounts](#-pre-configured-demo-accounts)
- [🧪 Testing & Quality Assurance](#-testing--quality-assurance)
- [📂 Repository Structure](#-repository-structure)
- [📜 License](#-license)

---

## ✨ Project Overview

**SkillsCraft AI (CraftConnect)** bridges the gap between ancient indigenous Indian craftsmanship and modern conscious commerce. Traditional artisans face severe exploitation from middlemen, who capture up to 80% of retail margins while erasing artisan identities.

SkillsCraft AI reverses this dynamic through:
1. **Direct Craft Acquisitions (Buy Flow)** with verified **88% direct artisan remittances** and transparent pricing breakdown.
2. **Slow-Craft Editorial Chronicles**: Immersive multimedia essays documenting ancient techniques (Gorakhpur wheel-thrown terracotta, 16-step Kutch natural indigo Ajrakh, 4,000-year-old Bastar lost-wax Dhokra, Saharanpur seasoned sheesham carving).
3. **Interactive AI Catalogue Assistant**: Powered by open-source large language models via OpenRouter, helping master artisans translate rough workshop notes into poetic, SEO-rich heritage product listings.
4. **Dedicated Dual Sanctuaries**: Tailored studio dashboards for master craftsmen (inventory, publishing, direct earnings) and patrons (order tracking, saved crafts, provenance certificates).

---

## 🌟 Key Innovations & Features

### 🛒 1. Direct Craft Acquisition & Checkout Flow
- **Interactive Checkout Card (`#buy-section`)**: Live client-side and server-side quantity adjustments with real-time INR total calculations.
- **88% Fair-Trade Transparency**: Dynamic visual breakdown displaying the exact amount remitted directly into the artisan's studio bank account.
- **Inventory & Stock Management**: Real-time stock decrementing that automatically transitions pieces to *Archival / Out of Stock* when inventory reaches zero.
- **Flexible Payment Options**: Supports UPI, Cash on Delivery / Handcraft Inspection, and Card transactions.

### 📜 2. Craft Chronicles & Editorial Journal
- **Heritage Storytelling**: Curated long-form stories chronicling artisanal traditions, mineral dye fermentation, and pit-kiln firings.
- **Artisan & Craft Linkage**: Seamless integration linking stories directly to featured craft pieces available for acquisition.
- **Filter by Tradition**: Dynamic filtering by craft disciplines including Ceramics, Textiles, Metalcraft, and Woodwork.

### 🤖 3. Open-Source AI Storytelling Assistant
- **Asynchronous LLM Generation**: Uses OpenRouter open-source endpoints (`nvidia/nemotron-3.5-super-vl:free` or Meta Llama / Mistral) to craft titles, descriptions, and material tags.
- **Studio Note Translation**: Turns colloquial Hindi or rough workshop bullet points into lyrical, collector-grade product narratives.
- **Resilient Fallback**: Built-in algorithmic fallback guarantees uninterrupted studio workflow even during API timeouts.

### 📊 4. Dedicated Artisan & Patron Workspaces
- **Artisan Atelier (`/accounts/artisan/`)**:
  - Live inventory tracking (in-stock, pending review, active in catalogue).
  - Studio Orders & Direct Remittances ledger with buyer destination and 88% payout metrics.
  - Interactive AI publishing form with real-time suggestion insertion.
- **Patron Sanctuary (`/accounts/buyer/`)**:
  - Acquired pieces tracker with order IDs, fulfillment stages, and artisan origin.
  - Saved crafts bookmark archive and AI-curated recommendations.

---

## 🏛️ System Architecture

```mermaid
graph TD
    Client[Web Browser / Mobile Client] -->|HTTP / HTTPS| Django[Django 5.1 Application Server]
    
    subgraph Core Apps
        Django --> Marketplace[marketplace App: Crafts, Stories, Orders]
        Django --> Accounts[accounts App: Roles, Profiles, Studio]
    end
    
    subgraph Data & Storage
        Marketplace --> DB[(PostgreSQL / Supabase)]
        Accounts --> DB
        Django --> Media[Media Storage: Unsplash Heirlooms]
    end

    subgraph External Intelligence
        Marketplace --> OpenRouter[OpenRouter AI: Nemotron / Llama / Mistral]
    end
```

---

## 🛠️ Tech Stack

| Domain | Technology | Description |
|---|---|---|
| **Backend** | Python 3.11+, Django 5.1 | High-performance Python web framework |
| **Database** | PostgreSQL 15+ (Supabase) | Production-ready relational DB with SSL & connection pooling |
| **Dev Database** | SQLite 3 | Zero-setup local development fallback (`USE_SQLITE=True`) |
| **Database Adapter** | `psycopg[binary] 3.3+`, `dj-database-url` | Fast, modern PostgreSQL driver with connection pooling |
| **AI / LLM** | OpenRouter (`nvidia/nemotron-3.5-super-vl:free`) | Open-source LLM pipeline for craft copy generation |
| **Frontend** | Django Templates, Tailwind CSS (CDN), Material Symbols | Warm terracotta & forest green aesthetic with Playfair Display typography |
| **Image Pipeline** | Pillow (PIL) | Automated image handling and profile uploads |

---

## 🚀 Quickstart & Installation

### Prerequisites
- Python 3.11 or higher
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/AllenLenoy/SkillsCraft-AI.git
cd SkillsCraft-AI
```

### 2. Create and Activate Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the template configuration file:
```bash
cp .env.example .env
```
Open `.env` in your editor and configure your secrets (OpenRouter API key, database settings). For immediate local testing, `USE_SQLITE=True` is enabled by default.

### 5. Apply Migrations & Seed Sample Heritage Data
```bash
# Run database migrations
python manage.py migrate

# Populate realistic artisans, crafts, stories, and sample orders
python manage.py seed_data
```

### 6. Launch the Development Server
```bash
python manage.py runserver
```
Navigate to **`http://127.0.0.1:8000/`** in your browser.

---

## ⚡ Supabase PostgreSQL Setup

SkillsCraft AI is built natively for Supabase PostgreSQL.

1. Create a project at [supabase.com](https://supabase.com).
2. Go to **Project Settings > Database > Connection string > URI** and copy your URI:
   ```text
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```
3. Update your `.env`:
   ```env
   USE_SQLITE=False
   DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
   ```
4. Run migrations on your Supabase instance:
   ```bash
   python manage.py migrate
   python manage.py seed_data
   ```

---

## 🤖 Open-Source AI Service Integration

The platform integrates open-source language models via OpenRouter to empower grassroots artisans.

Add your OpenRouter key to `.env`:
```env
AI_PROVIDER=openrouter
AI_BASE_URL=https://openrouter.ai/api/v1
AI_API_URL=https://openrouter.ai/api/v1/chat/completions
AI_MODEL=nvidia/nemotron-3.5-super-vl:free
AI_API_KEY=sk-or-v1-your_openrouter_api_key_here
```

To test the AI assistant directly from your terminal:
```bash
python manage.py verify_ai
```

---

## 👥 Pre-configured Demo Accounts

All demo accounts are stored directly in your **Supabase PostgreSQL** database:

| Role | Username | Password | Notes & Studio |
|---|---|---|---|
| **Admin Curator** | `admin` | `admin123` | Full access to Django admin & moderation |
| **Master Artisan 1** | `ramesh_artisan` | `artisan123` | Mati & Agni Atelier (Gorakhpur Terracotta) |
| **Master Artisan 2** | `fatima_handloom` | `artisan123` | Kutch Heritage Handloom Guild (Ajrakh & Chanderi Silk) |
| **Master Artisan 3** | `somnath_dhokra` | `artisan123` | Bastar Lost-Wax Bronze Guild (Tribal Dhokra) |
| **Master Artisan 4** | `iqbal_woodcraft` | `artisan123` | Saharanpur Woodwright Guild (Sheesham Jali & Walnut) |
| **Master Artisan 5** | `leela_crafts` | `artisan123` | Royal Heritage Atelier (Jaipur Blue Pottery & Filigree) |
| **Conscious Buyer 1** | `priya_buyer` | `buyer123` | Priya Sharma (Bengaluru) - Pre-populated orders |
| **Conscious Buyer 2** | `ananya_buyer` | `buyer123` | Ananya Sen (New Delhi) - Active orders & bookmarks |
| **Conscious Buyer 3** | `vikram_buyer` | `buyer123` | Vikram Mehta (Mumbai) - Architectural patron orders |

---

## 🧪 Testing & Quality Assurance

SkillsCraft AI maintains a robust test suite covering models, forms, AI service integration, security, permissions, and direct acquisition flows.

Run all tests:
```bash
python manage.py test
```

### Test Coverage Highlights
- ✅ **`ProductBuyAndOrderTests`**: Authenticated purchases, stock decrementing, zero-stock availability handling, 88% artisan share calculation.
- ✅ **`StoryModelAndViewsTests`**: Journal list, slug routing, category filtering, and product linkage.
- ✅ **`ArtisanStudioSecurityTests`**: Role-based access control, seller-only view guards.
- ✅ **`MarketplaceRoutingAndFormTests`**: URL reversing, search queries, validation.

---

## 📂 Repository Structure

```text
SkillsCraft-AI/
├── accounts/                  # User accounts, Artisan profiles, authentication & dashboards
│   ├── models.py              # ArtisanProfile model and signals
│   ├── views.py               # Auth, BuyerDashboard, ArtisanStudio views
│   └── tests.py               # Account permissions & role tests
├── craftconnect/              # Django core configuration
│   ├── settings.py            # Settings (PostgreSQL/Supabase + SQLite fallback)
│   ├── urls.py                # Global URL router
│   └── wsgi.py                # Production WSGI application
├── marketplace/               # Core commerce, editorial journal & ordering engine
│   ├── ai_service.py          # OpenRouter LLM integration & prompt engineering
│   ├── models.py              # Category, Product, Story, Order models
│   ├── views.py               # Catalog, ProductDetail, ProductBuy, StoryListView
│   ├── forms.py               # BuyOrderForm, ProductSearchForm
│   ├── admin.py               # Rich Django Admin interfaces
│   ├── tests.py               # 40 comprehensive unit & integration tests
│   └── management/commands/   # seed_data and verify_ai CLI commands
├── templates/                 # Semantic HTML5 templates with rich micro-animations
│   ├── base.html              # Base shell with navigation and toast notifications
│   ├── marketplace/           # home, product_detail, product_catalog, stories
│   └── accounts/              # buyer_dashboard, artisan_dashboard, auth
├── static/                    # Custom CSS, fonts, and client scripts
├── requirements.txt           # Production Python dependencies
├── .env.example               # Sanitized environment template
└── README.md                  # Project documentation
```

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

<div align="center">
  <sub>Crafted with passion for authentic Indian artisan heritage and equitable fair-trade commerce.</sub>
</div>