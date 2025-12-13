# 🚀 Vercel Environment Variables Setup

## Your Database Connection String
```
postgresql://neondb_owner:npg_KEBtonD1G4yC@ep-plain-pond-ahlps5ul-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require
```

---

## 📋 Add These 3 Variables to Vercel

### Go to: https://vercel.com/dashboard
1. Click on your **truck-productivity** project
2. Click **Settings** → **Environment Variables**
3. Add these variables:

---

### ✅ Variable 1: DATABASE_URL
- **Name:** `DATABASE_URL`
- **Value:** 
```
postgresql://neondb_owner:npg_KEBtonD1G4yC@ep-plain-pond-ahlps5ul-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require
```
- **Environments:** ✓ Production, ✓ Preview, ✓ Development

---

### ✅ Variable 2: DEBUG
- **Name:** `DEBUG`
- **Value:** `False`
- **Environments:** ✓ Production

---

### ✅ Variable 3: SECRET_KEY
- **Name:** `SECRET_KEY`
- **Value:** Generate at https://djecrety.ir/ (copy the generated key)
- **Environments:** ✓ Production, ✓ Preview, ✓ Development

---

## 🔄 After Adding Variables

1. Go to **Deployments** tab
2. Click **"..."** on latest deployment
3. Click **"Redeploy"**

✅ Your app will now work!
