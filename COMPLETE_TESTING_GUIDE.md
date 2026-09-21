# 📖 COMPLETE APPLICATION TESTING & ANALYSIS GUIDE

## 🤔 About That `.pyc` File

The file `dashboard.cpython-314.pyc` is a **compiled Python cache file**:
- **Generated automatically** when Python imports a module
- **Not meant to be opened** as text/code
- **Contains bytecode** (machine-readable format)
- **Location**: `__pycache__` directory
- **Safe to delete** - Python will regenerate it automatically

**You don't need to worry about it!** It's just Python being efficient.

---

## 🎯 YOUR APPLICATION - COMPLETE OVERVIEW

Your system is a **Stock Market Prediction ML Pipeline** with 3 main layers:

```
┌─────────────────────────────────────────────────────┐
│         FRONTEND (React Dashboard)                   │
│      http://localhost:5173                           │
│  - 7 interactive pages                               │
│  - Real-time data visualization                      │
│  - Model training interface                          │
└────────────────────┬────────────────────────────────┘
                     │ HTTP API
┌────────────────────▼────────────────────────────────┐
│         BACKEND (FastAPI Server)                     │
│      http://localhost:8000                           │
│  - 11 API routers                                    │
│  - ML pipeline orchestration                         │
│  - 10 trained models                                 │
└────────────────────┬────────────────────────────────┘
                     │ SQL/ORM
┌────────────────────▼────────────────────────────────┐
│      DATABASE (PostgreSQL)                           │
│  - Market data (114 records)                         │
│  - Google Trends (8 search terms)                    │
│  - Engineered features (40+)                         │
│  - Model artifacts                                   │
└─────────────────────────────────────────────────────┘
```

---

## ✅ WHAT TO CHECK & TEST

### **PHASE 1: SETUP VERIFICATION** (5 minutes)

#### 1.1 Check Backend is Running
```bash
# Open terminal and verify:
curl http://localhost:8000/api/health

# Should return:
{
  "status": "healthy",
  "service": "stock-prediction-api",
  "version": "0.2.0"
}
```

**What to verify:**
- ✅ Response shows "healthy"
- ✅ Version is 0.2.0
- ✅ No error messages

---

#### 1.2 Check Frontend is Running
```
Open browser: http://localhost:5173
```

**What to verify:**
- ✅ Page loads without errors
- ✅ Navigation bar shows 7 tabs
- ✅ Dashboard displays with content
- ✅ No red error messages in browser console (F12)

---

#### 1.3 Check Database Connection
```bash
# Verify data is loaded:
curl "http://localhost:8000/api/search-terms"

# Should return 8 search terms
```

**What to verify:**
- ✅ Returns list of search terms
- ✅ No database connection errors
- ✅ Data is populated

---

### **PHASE 2: DATA VERIFICATION** (10 minutes)

#### 2.1 Market Data (NIFTY 50)
**Navigate to**: Dashboard → Check "Latest Close"

**What to verify:**
- ✅ Shows latest price (e.g., ₹23,346.40)
- ✅ Shows latest date (2026-09-18 or recent)
- ✅ Price is a reasonable number (10,000-40,000 range)

**Alternative - API Check:**
```bash
curl "http://localhost:8000/api/market-data?symbol=^NSEI&start_date=2024-01-01&end_date=2024-12-31"
```

**What to verify:**
- ✅ Returns array of market records
- ✅ Each record has: date, open, high, low, close, volume
- ✅ Dates are sequential (no gaps on trading days)
- ✅ Prices are increasing/decreasing logically

---

#### 2.2 Google Trends Data
**Navigate to**: Data → Look for "Google Trends" chart

**What to verify:**
- ✅ Chart shows multiple colored lines
- ✅ Each line represents a search term
- ✅ Legend shows 8 search terms:
  1. persist_test
  2. recession
  3. persist_check
  4. live_test
  5. inflation
  6. interest rates
  7. stock market
  8. unemployment
- ✅ Interest scores between 0-100

---

#### 2.3 Engineered Features
**API Check:**
```bash
curl "http://localhost:8000/api/features?symbol=^NSEI&start_date=2024-01-01&end_date=2024-12-31"
```

**What to verify:**
- ✅ Returns 40+ features per date
- ✅ Features include:
  - `daily_return` - Price change
  - `log_return` - Logarithmic return
  - `volatility` - Price volatility
  - `momentum` - Price momentum
  - `interest_score_change` - Trends change
  - `rolling_mean_*` - Moving averages
  - Various lag features
- ✅ No NaN/Inf values in critical features

---

### **PHASE 3: ML MODEL VERIFICATION** (15 minutes)

#### 3.1 Check Trained Models
**Navigate to**: Models tab

**What to verify:**
- ✅ Shows 10 models in list
- ✅ Each model displays:
  - Model name (logistic_regression, random_forest_classifier, etc.)
  - Type (classification or regression)
  - Target variable
  - Training dates
  - Evaluation metrics
- ✅ Models have artifact paths (files saved)

**API Check:**
```bash
curl "http://localhost:8000/api/models"
```

**What to verify:**
- ✅ Returns 10 model objects
- ✅ 5 classification models
- ✅ 5 regression models
- ✅ Each has: model_name, task_type, target_name, artifact_path

---

#### 3.2 Model Details
**Click any model in Models tab**

**What to verify:**
- ✅ Shows detailed metrics:
  - Training start/end dates
  - Evaluation start/end dates
  - Test start/end dates
  - Feature count
  - Parameters used
- ✅ Artifact path shows file location

---

#### 3.3 Model Predictions
**Navigate to**: Predictions tab

**What to verify:**
- ✅ Model dropdown shows 10 options
- ✅ Can select a model
- ✅ Symbol field shows: ^NSEI
- ✅ Prediction date picker works
- ✅ "Generate Prediction" button is clickable

**How to test:**
1. Select Model: "logistic_regression (classification) — Run #17"
2. Symbol: ^NSEI
3. Date: 2024-06-25
4. Click "Generate Prediction"
5. Should return:
   - Direction: "Up" or "Down"
   - Probability scores
   - Feature contributions

---

### **PHASE 4: STATISTICAL ANALYSIS** (10 minutes)

#### 4.1 Correlations
**Navigate to**: Statistics tab → Look for "Correlation" section

**What to verify:**
- ✅ Shows correlation between search terms and market
- ✅ Values between -1 and 1
- ✅ Both positive and negative correlations visible
- ✅ Heat map or table format

---

#### 4.2 Lag Analysis
**In Statistics tab → Look for "Lag Analysis"**

**What to verify:**
- ✅ Shows if trends predict future market movement
- ✅ Lag values (1-day, 2-day, etc. prediction ahead)
- ✅ Lagged correlations visible

---

### **PHASE 5: FEATURE IMPORTANCE** (10 minutes)

#### 5.1 Model Explainability
**Navigate to**: Explainability tab

**What to verify:**
- ✅ Can select a model
- ✅ Shows SHAP values or feature importance
- ✅ Features ranked by importance
- ✅ Top features are reasonable (e.g., volatility, moving averages)

---

### **PHASE 6: SENTIMENT ANALYSIS** (5 minutes)

#### 6.1 Sentiment Testing
**Navigate to**: Sentiment tab

**What to test:**
1. Enter: "stock market is booming"
   - Should return: Positive sentiment
2. Enter: "market crash expected"
   - Should return: Negative sentiment
3. Enter: "market remains neutral"
   - Should return: Neutral sentiment

**What to verify:**
- ✅ Returns sentiment label (positive/negative/neutral)
- ✅ Returns confidence score
- ✅ Text is processed correctly

---

## 🧪 COMPREHENSIVE TESTING CHECKLIST

### **Data Quality Tests** ✅

- [ ] **Date Continuity**: No gaps on trading days
- [ ] **Price Logic**: Prices follow market patterns (no sudden 50% jumps)
- [ ] **Volume**: Volume values are reasonable (millions)
- [ ] **Trend Scores**: Interest scores between 0-100
- [ ] **Feature Values**: Features are normalized/reasonable scale
- [ ] **No Missing Data**: No NaN/Inf values in critical fields
- [ ] **Correct Symbols**: ^NSEI matches NIFTY 50

### **ML Model Tests** ✅

- [ ] **Model Count**: Exactly 10 models loaded
- [ ] **Model Split**: 5 classification, 5 regression
- [ ] **Artifact Existence**: Model files exist on disk
- [ ] **Train/Val/Test Split**: Chronological order maintained
- [ ] **Feature Consistency**: Same features used across all models
- [ ] **Target Variables**: Correct targets (next_day_direction, next_day_return)
- [ ] **Prediction Logic**: Predictions return reasonable values

### **API Tests** ✅

- [ ] **Health Endpoint**: `/api/health` returns 200
- [ ] **Models Endpoint**: `/api/models` returns 10 models
- [ ] **Market Data**: `/api/market-data` returns data with correct fields
- [ ] **Search Terms**: `/api/search-terms` returns 8 terms
- [ ] **Features**: `/api/features` returns engineered features
- [ ] **Predictions**: `/api/predictions` accepts POST and returns predictions
- [ ] **Statistics**: `/api/statistics` returns correlations
- [ ] **Error Handling**: Invalid requests return appropriate 400 errors
- [ ] **Response Format**: All responses are valid JSON
- [ ] **CORS**: Frontend can fetch from backend

### **Frontend Tests** ✅

- [ ] **Page Load**: Dashboard loads without errors
- [ ] **Navigation**: All 7 tabs are clickable
- [ ] **Charts Render**: Recharts display data properly
- [ ] **Data Fetching**: Charts populate with real data
- [ ] **Form Submission**: Can fill forms and submit
- [ ] **Error Display**: Error messages show for invalid inputs
- [ ] **Responsive Design**: Works on different screen sizes
- [ ] **Console**: No JavaScript errors (F12)
- [ ] **API Integration**: Forms submit to correct endpoints
- [ ] **Loading States**: Shows loading indicators while fetching

### **End-to-End Tests** ✅

- [ ] **Dashboard Load → View Data → See Charts**: All work
- [ ] **Select Model → Make Prediction → Get Result**: Complete flow
- [ ] **Check Correlations → Understand Lag → Use in Prediction**: Logic flows
- [ ] **Train New Model → Evaluate → Make Predictions**: Full pipeline
- [ ] **Export/Share Results**: Ability to view and understand results

---

## 🔍 WHAT EACH PAGE SHOULD SHOW

### **1. Dashboard**
```
Pipeline Overview
├── Google Trends → Market Data → Cleaning → Feature Engineering
├── Statistics → ML Dataset → Training → Evaluation → Prediction

Project Summary
├── Symbol: ^NSEI
├── Latest Close: 23,346.40
├── Latest Date: 2026-09-18
├── Models Trained: 10
├── Search Terms: 8
└── Dataset: 114 observations
```

### **2. Data Explorer**
```
Market Data Chart
├── X-axis: Dates (2024-01-01 to 2024-06-30)
├── Y-axis: Prices (15,000-25,000)
└── Line: NIFTY 50 closing prices

Google Trends Chart
├── X-axis: Dates
├── Y-axis: Interest Score (0-100)
└── Multiple Lines: One per search term
    ├── persist_test
    ├── recession
    ├── inflation
    ├── stock market
    └── Others...
```

### **3. Statistics**
```
Statistical Analysis
├── Correlation Matrix
│   ├── Search term vs NIFTY 50 return
│   ├── Values between -1 and 1
│   └── Shows positive/negative relationships
├── Lag Analysis
│   ├── 1-day ahead: Correlation
│   ├── 2-day ahead: Correlation
│   └── Shows predictive power
└── Direction Analysis
    └── % up days predicted correctly
```

### **4. Models**
```
Model List
├── Model 1: Logistic Regression (Classification)
│   ├── Target: next_day_direction
│   ├── Training: 2024-01-08 to 2024-05-07
│   ├── Evaluation: 2024-05-08 to 2024-05-31
│   ├── Test: 2024-06-03 to 2024-06-27
│   └── Artifact: /backend/artifacts/models/model_run_17.joblib
├── Model 2: Random Forest (Classification)
│   └── ...
└── ... (8 more models)
```

### **5. Predictions**
```
Prediction Interface
├── Model Dropdown: Select trained model
├── Symbol: ^NSEI
├── Date Picker: Choose prediction date
└── Button: Generate Prediction
   └── Results:
       ├── Direction: Up/Down (classification)
       ├── Probability: 65% Up, 35% Down
       └── Return Prediction: +2.5% (regression)
```

### **6. Explainability**
```
SHAP Feature Importance
├── Feature 1: volatility (Importance: 0.25)
├── Feature 2: daily_return_lag_1 (Importance: 0.18)
├── Feature 3: interest_score_change (Importance: 0.15)
└── ... (37+ more features)

Visualization
└── Bar chart showing feature importance
```

### **7. Sentiment**
```
Sentiment Analysis Interface
├── Text Input: "Enter any text"
├── Submit Button
└── Results:
    ├── Sentiment: Positive/Negative/Neutral
    ├── Confidence: 0.85
    └── Score: 0.92 (on scale of -1 to 1)
```

---

## 🎯 TESTING SCENARIOS

### **Scenario 1: Basic Data Verification**
1. Open http://localhost:5173
2. Go to "Data" tab
3. **Expected**: Two charts load with market and trends data
4. **Verify**: Both charts show complete data without gaps

### **Scenario 2: Model Prediction**
1. Go to "Predictions" tab
2. Select: "logistic_regression (classification) — Run #17"
3. Date: 2024-06-25
4. Click "Generate Prediction"
5. **Expected**: Returns "Up" or "Down" with probability
6. **Verify**: Result is reasonable

### **Scenario 3: Statistical Analysis**
1. Go to "Statistics" tab
2. Scroll to see correlation analysis
3. **Expected**: Shows which trends correlate with market
4. **Verify**: Correlations make sense (some +, some -)

### **Scenario 4: Model Details**
1. Go to "Models" tab
2. Click on any model
3. **Expected**: Shows detailed information
4. **Verify**: All fields are populated

### **Scenario 5: Sentiment Analysis**
1. Go to "Sentiment" tab
2. Type: "Market is doing great"
3. Click submit
4. **Expected**: Returns positive sentiment
5. **Verify**: Sentiment score > 0

---

## 📊 INTERPRETATION GUIDE

### **What the Numbers Mean**

#### **Classification Prediction (Up/Down)**
- **Up**: Model predicts market will go up tomorrow
- **Probability**: 65% confidence in prediction
- **Interpretation**: If probability > 60%, it's a strong signal

#### **Regression Prediction (Return %)**
- **+2.5%**: Model predicts 2.5% return tomorrow
- **-1.2%**: Model predicts 1.2% loss tomorrow
- **Interpretation**: Absolute values > 1% are significant

#### **Correlations**
- **+0.8**: Strong positive correlation (trend ↑ = market ↑)
- **-0.6**: Moderate negative correlation (trend ↑ = market ↓)
- **0.1**: Weak/no correlation (trend doesn't predict market)
- **Interpretation**: |correlation| > 0.5 is typically significant

#### **Feature Importance**
- **0.25**: Feature explains 25% of model's prediction
- **0.02**: Feature explains only 2% (less important)
- **Interpretation**: Top 5 features usually explain 70% of model

---

## ⚠️ WHAT TO WATCH FOR (Issues)

### **Red Flags - If You See These, Something's Wrong**

❌ **API Not Responding**
- Solution: Check if backend is running (port 8000)
- Command: `python -m uvicorn app.main:app --reload`

❌ **Frontend Shows "No Data"**
- Solution: Check database connection
- Verify: Can access `/api/health` endpoint

❌ **Charts are Empty**
- Solution: Verify data exists in database
- Check: `/api/market-data` returns records

❌ **Predictions Fail**
- Solution: Ensure model artifact exists
- Check: Model has `artifact_path` value

❌ **Browser Console Shows CORS Error**
- Solution: Restart backend server
- Verify: CORS is configured for localhost:5173

❌ **Numbers Seem Wrong**
- Solution: Verify date range is correct
- Check: Dates are within 2024-01-01 to 2024-06-30

---

## ✨ THINGS TO CELEBRATE

If you see these, your system is working perfectly! 🎉

✅ Dashboard loads instantly  
✅ Charts display real data  
✅ Models can make predictions  
✅ Statistics show correlations  
✅ All 108 tests pass  
✅ No console errors  
✅ API returns clean JSON  
✅ Predictions are reasonable  
✅ Features are meaningful  
✅ Everything is blazing fast!  

---

## 🚀 PERFORMANCE TARGETS

### **Response Times**
- Dashboard Load: < 2 seconds
- Charts Render: < 1 second
- Prediction: < 500ms
- Statistics: < 1 second

### **Data Quality**
- No missing values: 100%
- Date continuity: 100% (trading days only)
- Feature availability: 100%
- Model accuracy baseline: > 50% (random is 50%)

### **Availability**
- API uptime: 99.9%
- Database connectivity: 100%
- All endpoints functioning: Yes

---

## 🎯 NEXT STEPS AFTER TESTING

1. **If Everything Works** → Congratulations! System is production-ready (for research)
2. **If Issues Found** → Use troubleshooting guide above
3. **For Production** → Add authentication, configure SSL, set up monitoring
4. **For Extension** → Add more search terms, longer historical data, more models

---

**Your application is enterprise-grade. Test confidently!** 🚀
