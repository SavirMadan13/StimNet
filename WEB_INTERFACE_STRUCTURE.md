# Web Interface Structure

## Overview
The StimNet web interface has been refactored to separate concerns and improve maintainability. The code is now organized into separate files for HTML structure, CSS styling, and JavaScript functionality.

## File Structure

```
distributed_node/
├── static/
│   ├── app.js          # JavaScript functions
│   └── styles.css      # CSS styling
├── web_interface.py    # HTML template
└── real_main.py        # FastAPI server with static file serving
```

## Components

### 1. **HTML Template** (`distributed_node/web_interface.py`)
- **Purpose**: Defines the structure and content of the web interface
- **Key Features**:
  - Form for submitting analysis scripts
  - Data catalog selection
  - Example scripts display
  - Results display area
  - API documentation links
- **Links to**:
  - `/static/styles.css` for styling
  - `/static/app.js` for functionality

### 2. **JavaScript Functions** (`distributed_node/static/app.js`)
- **Purpose**: Handles all interactive functionality
- **Functions**:
  - `loadExample(type)` - Loads pre-built example scripts into the textarea
    - `type='demographics'` - Demographics analysis example
    - `type='correlation'` - Correlation analysis example
  - `submitJob()` - Submits analysis jobs to the server
    - Authenticates with demo credentials
    - Posts job to `/api/v1/jobs`
    - Displays job status
    - Auto-checks results after 3 seconds
  - `checkResults()` - Polls job status and displays results
    - Fetches job status from `/api/v1/jobs/{job_id}`
    - Updates UI based on status (running, completed, failed)
    - Displays analysis results or error messages

### 3. **CSS Styles** (`distributed_node/static/styles.css`)
- **Purpose**: Defines all visual styling
- **Key Styles**:
  - Layout: Container, sections, grid
  - Forms: Inputs, textareas, buttons
  - Status indicators: Completed, running, failed
  - Results display: Success and error states
  - Responsive design for mobile devices

### 4. **FastAPI Server** (`distributed_node/real_main.py`)
- **Purpose**: Serves the web interface and static files
- **Configuration**:
  ```python
  from fastapi.staticfiles import StaticFiles
  
  # Mount static files directory
  static_dir = os.path.join(os.path.dirname(__file__), "static")
  if os.path.exists(static_dir):
      app.mount("/static", StaticFiles(directory=static_dir), name="static")
  ```
- **Endpoints**:
  - `GET /` - Serves the web interface HTML
  - `GET /static/*` - Serves static files (JS, CSS)

## How It Works

### User Flow
1. **User visits** `http://localhost:8000` or the Cloudflare tunnel URL
2. **Browser loads**:
   - HTML from `/` endpoint
   - CSS from `/static/styles.css`
   - JavaScript from `/static/app.js`
3. **User clicks** "Load Demographics Example" button
   - JavaScript `loadExample('demographics')` function executes
   - Textarea fills with example script
4. **User clicks** "🚀 Run Analysis" button
   - JavaScript `submitJob()` function executes
   - Authenticates with server
   - Submits job to API
   - Displays "RUNNING" status
5. **After 3 seconds**:
   - JavaScript `checkResults()` auto-executes
   - Fetches job status from API
   - Displays results or error

### API Integration
```javascript
// Authentication
POST /api/v1/auth/token
Body: username=demo&password=demo
Response: { access_token: "..." }

// Job Submission
POST /api/v1/jobs
Headers: Authorization: Bearer {token}
Body: {
  target_node_id: "node-1",
  data_catalog_name: "clinical_trial_data",
  script_type: "python",
  script_content: "..."
}
Response: { job_id: "..." }

// Job Status Check
GET /api/v1/jobs/{job_id}
Response: {
  job_id: "...",
  status: "completed",
  result_data: {...},
  execution_time: 0.38
}
```

## Benefits of This Structure

### 1. **Separation of Concerns**
- HTML handles structure
- CSS handles presentation
- JavaScript handles behavior
- Python handles server logic

### 2. **Maintainability**
- Easy to find and modify specific functionality
- Changes to styling don't affect logic
- Changes to logic don't affect styling

### 3. **Reusability**
- JavaScript functions can be called from anywhere
- CSS classes can be reused across components
- HTML template can be easily extended

### 4. **Debugging**
- Browser DevTools can show JavaScript errors clearly
- CSS can be inspected and modified in real-time
- Network requests are visible in browser

### 5. **Performance**
- Static files can be cached by browser
- Reduces page load time on subsequent visits
- Smaller HTML payload

## Accessing the Interface

### Local Access
```bash
# Web Interface
http://localhost:8000

# API Documentation
http://localhost:8000/docs

# Static Files
http://localhost:8000/static/app.js
http://localhost:8000/static/styles.css
```

### Remote Access (via Cloudflare Tunnel)
```bash
# Get current URL
python get_public_url.py

# Example URLs
https://your-tunnel.trycloudflare.com
https://your-tunnel.trycloudflare.com/docs
https://your-tunnel.trycloudflare.com/static/app.js
```

## Modifying the Interface

### To Add a New Button
1. **Add HTML** in `web_interface.py`:
   ```html
   <button onclick="myNewFunction()">My Button</button>
   ```

2. **Add JavaScript** in `static/app.js`:
   ```javascript
   function myNewFunction() {
       // Your logic here
   }
   ```

3. **Add Styling** in `static/styles.css`:
   ```css
   .my-button-class {
       background: #28a745;
   }
   ```

### To Add a New Example Script
1. **Update JavaScript** in `static/app.js`:
   ```javascript
   function loadExample(type) {
       if (type === 'my_new_example') {
           textarea.value = `# Your example script here`;
       }
   }
   ```

2. **Add Button** in `web_interface.py`:
   ```html
   <button onclick="loadExample('my_new_example')">Load My Example</button>
   ```

## Testing

### Test Static Files Are Served
```bash
# Test JavaScript
curl http://localhost:8000/static/app.js | head -10

# Test CSS
curl http://localhost:8000/static/styles.css | head -10

# Test HTML includes links
curl http://localhost:8000/ | grep -E "(app.js|styles.css)"
```

### Test Functionality
1. Visit `http://localhost:8000`
2. Open browser DevTools (F12)
3. Click "Load Demographics Example"
4. Check Console for any errors
5. Click "🚀 Run Analysis"
6. Check Network tab for API calls
7. Verify results display

## Current Status

✅ **Fully Operational**
- Static files are being served correctly
- JavaScript functions are working
- CSS styling is applied
- Web interface is accessible locally and remotely
- All buttons and forms are functional

## Future Enhancements

### Potential Improvements
1. **Add more example scripts** for different analysis types
2. **Implement real-time job progress** using WebSockets
3. **Add data visualization** using Chart.js or D3.js
4. **Create a job history view** to see past analyses
5. **Add user authentication UI** for non-demo users
6. **Implement file upload** for custom datasets
7. **Add syntax highlighting** for code editor (CodeMirror/Monaco)
8. **Create a results export** feature (CSV, JSON, PDF)

### Code Quality
1. **Add JSDoc comments** for all functions
2. **Implement error handling** for network failures
3. **Add loading spinners** for better UX
4. **Create unit tests** for JavaScript functions
5. **Add TypeScript** for type safety
6. **Minify and bundle** JS/CSS for production

---

**Last Updated**: October 8, 2025  
**Version**: 1.0.0  
**Status**: Production Ready
