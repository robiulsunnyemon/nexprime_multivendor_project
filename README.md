# NexPrime - Multi-Vendor E-commerce Platform

NexPrime is a high-performance, scalable multi-vendor e-commerce API built with **FastAPI**, **Prisma (Python)**, and **PostgreSQL**. It supports multiple user roles, real-time communication, a comprehensive wallet system, and a unique C2C marketing product marketplace.

---

## 🚀 Technology Stack & Integrations

- **Backend Framework**: FastAPI (Asynchronous Python)
- **Database**: PostgreSQL with Prisma Client Python (ORM)
- **Media Management**: **Cloudinary** (Automated storage for Images, Audio, and Video)
- **Real-Time Communication**: **WebSockets** (Chat) & **LiveKit** (Video Streaming)
- **Payments**: **Stripe** (Secure checkout & Automated Commission Splitting)
- **Authentication**: JWT with **SMTP Email OTP** verification
- **Validation**: Pydantic v2
- **Infrastructure**: Docker & Poetry

---

## 📂 Project Structure

```text
nexprime/
├── app/
│   ├── admin/             # System settings, dashboard, & platform commissions
│   ├── advertisement/     # Banner/Ad management
│   ├── auth/              # JWT, OTP, & Multi-role registration
│   ├── cart/              # Persistent shopping cart
│   ├── category/          # Main & Sub-category hierarchy
│   ├── chat/              # WebSocket-based real-time messaging
│   ├── core/              # Global config, Cloudinary/Email services, & Security
│   ├── database/          # Prisma client initialization
│   ├── faq/               # FAQ management
│   ├── live/              # LiveKit-powered video streaming metadata
│   ├── marketing_product/ # C2C Marketplace (Customer goods)
│   ├── order/             # Orders, Sub-orders, & Stripe integration
│   ├── product/           # Vendor product management & advanced search
│   ├── static_page/       # CMS for Pages (Policy, Terms, etc.)
│   ├── store/             # Store profiles & follower system
│   ├── user/              # User profiles & Wallet system
│   ├── vendor/            # Vendor KYC & Store settings
│   └── main.py            # API Entry point
├── prisma/
│   └── schema.prisma      # Database models
├── .env                   # Configuration secrets
└── pyproject.toml         # Dependencies
```

---

## 👥 Roles & Permissions

| Role | Description | Key Permissions |
| :--- | :--- | :--- |
| **CUSTOMER** | Regular buyer | Browse, cart, orders, wallet, C2C marketing, chat, join live streams. |
| **VENDOR** | Store owner | Managed stores, upload products, fulfill sub-orders, start live streams. |
| **ADMIN** | Platform owner | Verify KYC, manage commissions, toggle registration, view dashboard. |

---

## 🛠 Advanced Modules

### 1. Real-Time Chat (`/chat`)
- **WebSocket Power**: Instant messaging between customers and vendors.
- **Multimedia Support**: Send Images, Audio snippets, and Videos directly in chat.
- **Service**: Integrated with **Cloudinary** for secure media hosting.
- **History**: Full chat history and active user tracking.

### 2. Live Video Streaming (`/live-streams`)
- **Broadcasting**: Vendors can host live shows to demonstrate products.
- **Interactive**: Real-time view counts and viewer tokens via **LiveKit**.
- **Engagement**: Customers can join active streams to get special offers.

### 3. Payment & Split Earnings (`/orders`)
- **Stripe Integration**: Secure payment intent for orders and wallet top-ups.
- **Automated Commission**: Platform automatically deducts a percentage (set by Admin) from each sub-order.
- **Vendor Earnings**: Logic calculates net earnings for vendors after fees.
- **Payment Webhooks**: Real-time processing of successful transactions.

### 4. Customer Product Marketing (C2C) (`/marketing-products`)
- **User Marketplace**: Customers can list their own used/new goods.
- **Monetization**: Platform charges a small **Publishing Fee** (managed via Wallet).
- **Control**: Admin can enable/disable publishing and set fees.

### 5. Media & Notification Services
- **Cloudinary**: Handles all file uploads with automatic optimization.
- **Email OTP**: SMTP-based One-Time Passwords for registration and password resets.

---

## 📡 API Documentation (Key Endpoints)

### Authentication & Media

#### **Signup & Media Upload**
- **Endpoint**: `POST /auth/signup`
- **Output**: Returns success message; triggers an **Email OTP**.
- **Media**: KYC documents are automatically uploaded to **Cloudinary**.

#### **Verify OTP**
- **Endpoint**: `POST /auth/verify-otp`
- **Body**: `{"email": "...", "code": "123456"}`

### Real-Time & Streaming

#### **Join Chat (WebSocket)**
- **URL**: `ws://<domain>/chat/ws/<jwt_token>`
- **Format**: JSON messages with support for `TEXT`, `IMAGE`, `VIDEO`.

#### **Start Live Stream (Vendor)**
- **Endpoint**: `POST /live-streams`
- **Response**: Returns a **LiveKit Broadcaster Token**.

### Marketplace & Payments

#### **List Marketing Product (Customer)**
- **Endpoint**: `POST /marketing-products`
- **Note**: Deducts publishing fee from user **Wallet**.

#### **Checkout**
- **Endpoint**: `POST /orders`
- **Response**: Summary + Stripe `clientSecret` for payment.

---

## ⚙️ Setup

1. **Environment**: Configure `.env` with `CLOUDINARY_*`, `STRIPE_*`, `SMTP_*`, and `LIVEKIT_*`.
2. **Install**: `poetry install`
3. **DB Sync**: `prisma db push`
4. **Run**: `uvicorn app.main:app --reload`

---

*NexPrime: Bridging Vendors and Customers with Modern Tech.*
