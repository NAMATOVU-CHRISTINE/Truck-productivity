# PostgreSQL Setup Guide for Truck Productivity Dashboard

## ✅ What's Been Done

Your Django application has been configured to use:
- **PostgreSQL** in production (Vercel)
- **SQLite** in development (local)

The following changes were made:
1. ✅ Updated `requirements.txt` with PostgreSQL dependencies
2. ✅ Modified `settings.py` to support both databases
3. ✅ Added environment variable support for secure configuration
4. ✅ Created `.env.example` for documentation

---

## 🚀 Next Steps

### Step 1: Create a PostgreSQL Database

Choose one of these FREE PostgreSQL providers:

#### Option A: **Neon** (Recommended)
1. Go to https://neon.tech/
2. Sign up for a free account
3. Create a new project: "Truck Productivity"
4. Copy the connection string (looks like):
   ```
   postgresql://username:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require
   ```

#### Option B: **Supabase**
1. Go to https://supabase.com/
2. Create a new project
3. Go to Settings → Database
4. Copy the connection string (URI format)

#### Option C: **Vercel Postgres**
1. Go to your Vercel dashboard
2. Go to Storage → Create Database → Postgres
3. Connect it to your project
4. Copy the connection string

---

### Step 2: Set Up Environment Variables in Vercel

1. Go to your Vercel project dashboard
2. Navigate to: **Settings → Environment Variables**
3. Add these variables:

| Variable Name | Value | Environment |
|---------------|-------|-------------|
| `DATABASE_URL` | Your PostgreSQL connection string | Production |
| `DEBUG` | `False` | Production |
| `SECRET_KEY` | Generate a new secret key* | Production |

*Generate a secret key: https://djecrety.ir/

---

### Step 3: Install New Dependencies Locally

Run in your terminal:
```bash
cd "/home/christine/Documents/Project/Truck productivity"
pip install -r requirements.txt
```

---

### Step 4: Migrate Your Data to PostgreSQL

#### Option A: Start Fresh (Recommended for Testing)
1. The database will be created automatically on first deploy
2. You can add data through the Django admin or upload files

#### Option B: Transfer Existing Data
If you want to keep your current SQLite data:

1. **Export data from SQLite:**
   ```bash
   python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > data_backup.json
   ```

2. **Set up local PostgreSQL connection** (create a `.env` file):
   ```
   DATABASE_URL=your_postgresql_connection_string
   ```

3. **Migrate and load data:**
   ```bash
   python manage.py migrate
   python manage.py loaddata data_backup.json
   ```

---

### Step 5: Deploy to Vercel

1. **Commit and push your changes:**
   ```bash
   git add .
   git commit -m "Configure PostgreSQL for production"
   git push
   ```

2. **Vercel will automatically redeploy**
3. **Check deployment logs** for any issues

---

### Step 6: Run Migrations on Vercel

After the first deployment, you need to run migrations:

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Login and link project:
   ```bash
   vercel login
   vercel link
   ```

3. Run migrations:
   ```bash
   vercel env pull .env.production
   python manage.py migrate --settings=truck_productivity.settings
   ```

Alternatively, you can trigger migrations by adding a `build_files.sh` script that runs on each deployment.

---

## 🧪 Testing Locally

To test with PostgreSQL locally:

1. Create a `.env` file (not committed to git):
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/truck_productivity
   DEBUG=True
   SECRET_KEY=your-dev-secret-key
   ```

2. Run migrations:
   ```bash
   python manage.py migrate
   ```

3. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

4. Run the development server:
   ```bash
   python manage.py runserver
   ```

---

## 📝 Important Notes

- **Local Development**: Will use SQLite (no setup needed)
- **Production (Vercel)**: Will use PostgreSQL (requires DATABASE_URL)
- **Environment Variables**: Never commit `.env` file to git
- **Migrations**: Run migrations after every database schema change

---

## 🔧 Troubleshooting

### Issue: "unable to open database file"
- ✅ **Fixed!** This error won't occur anymore with PostgreSQL

### Issue: "connection to server failed"
- Check your DATABASE_URL is correct
- Ensure your PostgreSQL provider allows connections
- Check if SSL is required (add `?sslmode=require`)

### Issue: "no such table"
- Run migrations: `python manage.py migrate`
- Check if DATABASE_URL environment variable is set in Vercel

---

## ✨ What's Next?

Once you've completed these steps:
1. Your app will work on Vercel ✅
2. Data will persist across deployments ✅
3. You can scale without database issues ✅

Need help with any step? Just ask!
