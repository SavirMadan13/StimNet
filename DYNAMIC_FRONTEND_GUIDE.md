# Dynamic Frontend Guide

## Overview
Your StimNet web interface is now **dynamic** - it automatically loads data catalogs and other information from the API instead of using hardcoded values.

## 🎯 **What Changed**

### **Before (Static):**
```html
<!-- Hardcoded dropdown -->
<select id="catalog">
    <option value="clinical_trial_data">Clinical Trial Data (150 subjects)</option>
    <option value="imaging_data">Imaging Data (100 scans)</option>
    <option value="demo_dataset">Demo Dataset (50 records)</option>
</select>

<!-- Hardcoded catalog info -->
<div>
    <h4>🏥 Clinical Trial Data</h4>
    <p><strong>150 subjects</strong> - Parkinson's disease research</p>
</div>
```

### **After (Dynamic):**
```javascript
// Fetches from API on page load
async function loadDataCatalogs() {
    const response = await fetch('/api/v1/data-catalogs');
    const catalogs = await response.json();
    
    // Dynamically populates dropdown
    catalogs.forEach(catalog => {
        const option = document.createElement('option');
        option.value = catalog.name;
        option.textContent = `${catalog.name} (${catalog.description})`;
        catalogSelect.appendChild(option);
    });
}
```

## 🚀 **How It Works**

### **1. Page Load Sequence:**

```
User visits http://localhost:8000
    ↓
Browser loads HTML with empty/loading state
    ↓
JavaScript DOMContentLoaded event fires
    ↓
loadDataCatalogs() function executes
    ↓
Fetches GET /api/v1/data-catalogs
    ↓
Populates dropdown and info section dynamically
```

### **2. API Integration:**

The frontend now calls this API endpoint:
```bash
GET /api/v1/data-catalogs
```

**Response Format:**
```json
[
    {
        "id": 1,
        "name": "clinical_trial_data",
        "description": "Synthetic clinical trial dataset for Parkinson's disease research",
        "data_type": "tabular",
        "schema_definition": {...},
        "privacy_level": "high",
        "min_cohort_size": 10
    },
    {
        "id": 2,
        "name": "imaging_data",
        "description": "Neuroimaging scan metadata",
        "data_type": "tabular",
        "schema_definition": {...}
    }
]
```

### **3. Dynamic Elements:**

#### **A. Data Catalog Dropdown**
```javascript
// Location: distributed_node/static/app.js
// Function: loadDataCatalogs()

// Dynamically creates options:
<select id="catalog">
    <option value="clinical_trial_data">clinical_trial_data (Synthetic clinical trial...)</option>
    <option value="imaging_data">imaging_data (Neuroimaging scan metadata)</option>
    <!-- More options added automatically -->
</select>
```

#### **B. Catalog Information Display**
```javascript
// Dynamically creates info cards:
<div class="grid">
    <div>
        <h4>🏥 clinical_trial_data</h4>
        <p><strong>Synthetic clinical trial dataset...</strong></p>
        <p>Type: tabular</p>
    </div>
    <div>
        <h4>🧠 imaging_data</h4>
        <p><strong>Neuroimaging scan metadata</strong></p>
        <p>Type: tabular</p>
    </div>
</div>
```

## 📝 **Adding New Data Catalogs**

### **The Old Way (Static):**
1. Edit `web_interface.py`
2. Add hardcoded HTML
3. Restart server
4. Hope you didn't forget anything

### **The New Way (Dynamic):**
1. Add data to database:
```python
from distributed_node.database import SessionLocal
from distributed_node.models import DataCatalog

db = SessionLocal()
new_catalog = DataCatalog(
    name="my_new_dataset",
    description="My awesome new dataset",
    data_type="tabular",
    schema_definition={"columns": ["id", "value"]}
)
db.add(new_catalog)
db.commit()
```

2. **That's it!** The frontend automatically shows it.

## 🔧 **How to Extend This Pattern**

### **Example: Dynamic Node Information**

**1. Create API endpoint** (in `distributed_node/real_main.py`):
```python
@app.get("/api/v1/node-info")
async def get_node_info(db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.node_id == settings.node_id).first()
    return {
        "node_id": node.node_id,
        "institution": node.institution_name,
        "status": "healthy",
        "capabilities": ["python", "r"],
        "data_catalogs_count": db.query(DataCatalog).count()
    }
```

**2. Add JavaScript function** (in `distributed_node/static/app.js`):
```javascript
async function loadNodeInfo() {
    try {
        const response = await fetch('/api/v1/node-info');
        const nodeInfo = await response.json();
        
        document.getElementById('node-id').textContent = nodeInfo.node_id;
        document.getElementById('institution').textContent = nodeInfo.institution;
        document.getElementById('catalog-count').textContent = nodeInfo.data_catalogs_count;
    } catch (error) {
        console.error('Error loading node info:', error);
    }
}

// Call on page load
document.addEventListener('DOMContentLoaded', function() {
    loadDataCatalogs();
    loadNodeInfo();  // Add this
});
```

**3. Update HTML** (in `distributed_node/web_interface.py`):
```html
<div class="header">
    <h1>🧠 StimNet Research Platform</h1>
    <p>Node: <span id="node-id">Loading...</span></p>
    <p>Institution: <span id="institution">Loading...</span></p>
    <p>Available Datasets: <span id="catalog-count">Loading...</span></p>
</div>
```

### **Example: Dynamic Job Statistics**

**1. API endpoint:**
```python
@app.get("/api/v1/stats")
async def get_stats(db: Session = Depends(get_db)):
    return {
        "total_jobs": db.query(Job).count(),
        "completed_jobs": db.query(Job).filter(Job.status == JobStatus.COMPLETED).count(),
        "failed_jobs": db.query(Job).filter(Job.status == JobStatus.FAILED).count(),
        "active_jobs": db.query(Job).filter(Job.status.in_([JobStatus.RUNNING, JobStatus.QUEUED])).count()
    }
```

**2. JavaScript:**
```javascript
async function loadStats() {
    const response = await fetch('/api/v1/stats');
    const stats = await response.json();
    
    document.getElementById('total-jobs').textContent = stats.total_jobs;
    document.getElementById('completed-jobs').textContent = stats.completed_jobs;
    document.getElementById('active-jobs').textContent = stats.active_jobs;
}

// Refresh stats every 10 seconds
setInterval(loadStats, 10000);
```

**3. HTML:**
```html
<div class="stats">
    <p>Total Jobs: <span id="total-jobs">0</span></p>
    <p>Completed: <span id="completed-jobs">0</span></p>
    <p>Active: <span id="active-jobs">0</span></p>
</div>
```

## 🎨 **Benefits of Dynamic Frontend**

### **1. Automatic Updates**
- Add new datasets → They appear automatically
- No code changes needed
- No server restart required (for data changes)

### **2. Consistency**
- Frontend always matches backend state
- No risk of hardcoded values being outdated
- Single source of truth (the database)

### **3. Scalability**
- Works with 3 datasets or 300 datasets
- No performance impact from large lists
- Easy to add pagination if needed

### **4. Maintainability**
- Less code to maintain
- Fewer places to update
- Easier to debug (check API response)

### **5. Flexibility**
- Can filter/sort catalogs dynamically
- Can show/hide based on permissions
- Can customize display per user

## 🧪 **Testing Dynamic Loading**

### **Test 1: Check API Response**
```bash
curl http://localhost:8000/api/v1/data-catalogs | python -m json.tool
```

Expected output:
```json
[
    {
        "id": 1,
        "name": "clinical_trial_data",
        "description": "Synthetic clinical trial dataset...",
        ...
    }
]
```

### **Test 2: Check Browser Console**
1. Open http://localhost:8000
2. Press F12 (DevTools)
3. Go to Console tab
4. Look for: `Loaded 3 data catalogs`

### **Test 3: Check Network Tab**
1. Open http://localhost:8000
2. Press F12 (DevTools)
3. Go to Network tab
4. Refresh page
5. Look for request to `/api/v1/data-catalogs`
6. Click on it to see response

### **Test 4: Verify Dropdown**
1. Open http://localhost:8000
2. Click on "Data Catalog" dropdown
3. Should see dynamically loaded options
4. Not "Loading datasets..."

## 🐛 **Troubleshooting**

### **Problem: Dropdown shows "Loading datasets..."**

**Possible causes:**
1. API endpoint not responding
2. JavaScript error preventing execution
3. CORS issue (unlikely for same-origin)

**Solution:**
```bash
# Check if API is working
curl http://localhost:8000/api/v1/data-catalogs

# Check browser console for errors (F12)
# Look for red error messages

# Check if JavaScript is loading
curl http://localhost:8000/static/app.js | grep loadDataCatalogs
```

### **Problem: Dropdown is empty**

**Possible causes:**
1. No data catalogs in database
2. API returning empty array
3. JavaScript error in forEach loop

**Solution:**
```bash
# Check database
sqlite3 distributed_node.db "SELECT name FROM data_catalogs;"

# If empty, run setup script
python examples/setup_demo_data.py
```

### **Problem: Old hardcoded values still showing**

**Possible causes:**
1. Browser cache
2. Server not restarted
3. Old JavaScript file cached

**Solution:**
```bash
# Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
# Or clear cache in DevTools

# Restart server
python restart_all.py
```

## 📊 **Current Dynamic Elements**

| Element | API Endpoint | Update Frequency | Fallback |
|---------|-------------|------------------|----------|
| Data Catalogs Dropdown | `/api/v1/data-catalogs` | On page load | Hardcoded 3 catalogs |
| Catalog Info Display | `/api/v1/data-catalogs` | On page load | Error message |

## 🚀 **Future Dynamic Elements**

Here are suggestions for what else could be made dynamic:

### **1. Real-time Job Status**
- Poll `/api/v1/jobs/{job_id}` every 2 seconds
- Update progress bar dynamically
- Show live execution logs

### **2. Available Script Types**
- Fetch from `/api/v1/capabilities`
- Show Python, R, SQL based on what's installed
- Hide unavailable options

### **3. User Permissions**
- Fetch from `/api/v1/user/permissions`
- Show/hide features based on role
- Customize UI per user

### **4. System Health**
- Poll `/health` endpoint
- Show server status, uptime, load
- Alert if system is degraded

### **5. Recent Jobs**
- Fetch from `/api/v1/jobs?limit=10`
- Show last 10 jobs in sidebar
- Click to view details

## 📖 **Code Locations**

| Component | File | Lines |
|-----------|------|-------|
| Dynamic catalog loading | `distributed_node/static/app.js` | 8-63 |
| Page initialization | `distributed_node/static/app.js` | 65-68 |
| Catalog dropdown HTML | `distributed_node/web_interface.py` | 39-44 |
| Catalog info display HTML | `distributed_node/web_interface.py` | 28-33 |
| API endpoint | `distributed_node/real_main.py` | ~120-130 |

## 🎓 **Learning Resources**

### **JavaScript Fetch API**
```javascript
// Basic fetch
fetch('/api/endpoint')
    .then(response => response.json())
    .then(data => console.log(data));

// Async/await (preferred)
async function getData() {
    const response = await fetch('/api/endpoint');
    const data = await response.json();
    return data;
}
```

### **DOM Manipulation**
```javascript
// Get element
const element = document.getElementById('myId');

// Update text
element.textContent = 'New text';

// Update HTML
element.innerHTML = '<p>New HTML</p>';

// Create element
const newDiv = document.createElement('div');
newDiv.textContent = 'Hello';
document.body.appendChild(newDiv);
```

### **Event Listeners**
```javascript
// On page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded!');
});

// On button click
document.getElementById('myButton').addEventListener('click', function() {
    console.log('Button clicked!');
});
```

## ✅ **Verification Checklist**

- [ ] API endpoint returns correct data
- [ ] JavaScript loads without errors
- [ ] Dropdown populates with catalogs
- [ ] Catalog info displays correctly
- [ ] Fallback works if API fails
- [ ] Console shows "Loaded X data catalogs"
- [ ] Network tab shows successful API call
- [ ] New catalogs appear automatically

---

**Last Updated**: October 8, 2025  
**Version**: 2.0.0 (Dynamic)  
**Status**: Fully Operational
