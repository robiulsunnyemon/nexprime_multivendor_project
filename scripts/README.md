# 📁 Scripts

This folder contains utility and management scripts for the Nexprime project.

---

## 🛡️ `create_admin.py` — Admin Account Creation Script

Run this script to interactively create an **Admin account** directly in the database.

### ✅ Prerequisites
- The `DATABASE_URL` must be correctly set in the `.env` file.
- The Prisma client must be generated:
  ```bash
  prisma generate
  ```

### ▶️ How to Run

From the **project root directory**:

```bash
# Recommended (using Poetry)
poetry run python scripts/create_admin.py

# Or directly
python scripts/create_admin.py
```

### 📝 Required Inputs
| Field        | Description                          |
|--------------|--------------------------------------|
| Full Name    | Admin's full name                    |
| Email        | Login email (must be unique)         |
| Phone Number | Phone number (must be unique)        |
| Password     | Minimum 6 characters                 |

### 🔐 Created Account Properties
- **Role**: `ADMIN`
- **Status**: `ACTIVE`
- **is_verified**: `True` (activated directly without OTP)
- Password is hashed using `bcrypt`.
