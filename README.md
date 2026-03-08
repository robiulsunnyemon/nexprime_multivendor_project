# NexPrime - Multi-Vendor E-commerce Platform

NexPrime is a high-performance, scalable multi-vendor e-commerce API built with **FastAPI**, **Prisma (Python)**, and **PostgreSQL**. It supports multiple user roles, real-time communication, a comprehensive wallet system, and a unique C2C marketing product marketplace.

## Technology Stack

- **Framework**: FastAPI (Asynchronous Python)
- **Database**: PostgreSQL
- **ORM**: Prisma Client Python
- **Authentication**: JWT (JSON Web Tokens) with OTP (One-Time Password) Verification
- **Validation**: Pydantic v2
- **Infrastructure**: Docker for containerization

---

## 📂 Project Structure

```text
nexprime/
├── app/
│   ├── admin/             # Admin-specific logic (settings, dashboard, marketing)
│   ├── advertisement/     # Banner and ad management
│   ├── auth/              # Authentication (JWT, OTP, Signup/Login)
│   ├── cart/              # Shopping cart management
│   ├── category/          # Category & Sub-category management
│   ├── chat/              # Real-time messaging (WebSocket/HTTP)
│   ├── core/              # Global config, security, and utility functions
│   ├── database/          # Prisma client initialization
│   ├── faq/               # Frequently Asked Questions management
│   ├── live/              # Live streaming metadata & tracking
│   ├── marketing_product/ # C2C Marketplace (Marketing Products)
│   ├── order/             # Orders, Sub-orders, Ratings & Stripe Integration
│   ├── product/           # Standard product management & advanced search
│   ├── static_page/       # CMS for Pages (Privacy Policy, Terms, etc.)
│   ├── store/             # Store profiles & follower system
│   ├── user/              # User profiles, verification, and Wallet system
│   ├── vendor/            # Vendor-specific logic (KYC, Store settings)
│   └── main.py            # API Entry point & Router registration
├── prisma/
│   └── schema.prisma      # Database schema and models
├── .env                   # Environment variables
├── Dockerfile             # Container configuration
└── pyproject.toml         # Python dependencies (Poetry)
```

---

## 👥 Roles & Permissions

| Role | Description | Key Permissions |
| :--- | :--- | :--- |
| **CUSTOMER** | Regular buyer | Browse products, place orders, chat with vendors, manage wallet, use C2C marketplace. |
| **VENDOR** | Store owner | Manage store profile, upload products, fulfill sub-orders, track earnings. |
| **ADMIN** | Platform owner | System settings, commission management, KYC verification, platform dashboard. |

---

## Core Modules

### 1. Authentication (`/auth`)
- **Signup**: Multi-step registration for Customers and Vendors.
- **OTP Verification**: Verifies email/phone during registration and password reset.
- **Login**: Issue Access and Refresh tokens.
- **Password Reset**: Secure flow via OTP and temporary reset tokens.

### 2. Vendor & Store Management (`/vendor`, `/store`)
- **KYC**: Vendors must upload documents for admin approval.
- **Store Profiles**: Localized store details, bio, and banners.
- **Followers**: Customers can follow stores to stay updated.

### 3. Product System (`/products`)
- **Categorization**: Multi-level categories (Main -> Sub).
- **Advanced Search**: Filter by price, category, size, color, and store.
- **Inventory**: Real-time stock tracking and inventory management.

### 4. Order & Payment Flow (`/orders`)
- **Cart**: Persistent shopping cart for customers.
- **Order Splitting**: A single customer order is split into **Sub-Orders** per vendor.
- **Split Payments**: Tracks vendor earnings and platform commissions automatically.
- **Ratings**: Post-delivery feedback and rating system.

### 5. C2C Marketing Products (`/marketing-product`)
- Allows users to list their own goods for sale (independent of formal stores).
- Requires a small publishing fee (managed via platform settings).

### 6. Wallet & Transactions (`/user/wallet`)
- Built-in wallet for each user.
- Tracks `TOPUP` and `FEE_DEDUCTION` (e.g., for marketing product fees).

---

## API Documentation (Endpoints)

### Authentication

#### **Register a Customer**
- **Endpoint**: `POST /auth/signup`
- **Type**: `multipart/form-data`
- **Input**:
  - `fullname`, `email`, `phonenumber`, `password`
  - `residentcard_frontside`, `residentcard_backside` (Files)
- **Response**: `{"message": "Registration successful. Please verify OTP."}`

#### **Login**
- **Endpoint**: `POST /auth/login`
- **Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "...",
    "refresh_token": "...",
    "user": { "id": 1, "role": "CUSTOMER", ... }
  }
  ```

### Products

#### **Create Product (Vendor Only)**
- **Endpoint**: `POST /vendor/products`
- **Headers**: `Authorization: Bearer <JWT>`
- **Input**: `name`, `basePrice`, `stockUnits`, `category_ids` (JSON Array), `images` (List of Files)
- **Response**: Standard product object with IDs and image URLs.

#### **Search Products**
- **Endpoint**: `GET /products/filter`
- **Queries**: `shop_id`, `subcategory_ids`, `size`, `color`
- **Example**: `/products/filter?subcategory_ids=1&size=XL`

### Orders

#### **Create Order**
- **Endpoint**: `POST /orders`
- **Body**:
  ```json
  {
    "deliveryAddressId": 1,
    "items": [
      { "productId": 10, "quantity": 2 }
    ]
  }
  ```
- **Response**: Full order summary with calculated totals and sub-orders.

---

## ⚙️ Setup & Installation

1. **Install Dependencies**:
   ```bash
   poetry install
   ```
2. **Setup Database**:
   ```bash
   prisma db push
   ```
3. **Run the Application**:
   ```bash
   uvicorn app.main:app --reload
   ```

---


