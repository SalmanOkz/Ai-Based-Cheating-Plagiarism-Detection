# Vision Guardian - AI-Based Cheating Detection System

A comprehensive AI-powered proctoring system for exam integrity monitoring.

## ✨ Features

### Vision-Based Detection

- **YOLO Object Detection**: Multi-person and prohibited item detection
- **Gaze Tracking**: Eye movement and head pose analysis
- **Real-time Monitoring**: Live video feed with AI annotations
- **Risk Scoring**: Unified risk assessment system

### Integrity Auditing

- **Text Analysis**: AI vs Human text detection
- **Code Plagiarism**: AST-based code similarity detection
- **Stylometry**: Writing style analysis

### Security Features

- File upload validation and size limits
- Path traversal prevention
- Secure temporary file handling
- Thread-safe operations

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Webcam
- 8GB RAM minimum (16GB recommended)
- GPU recommended for better performance

### Installation

1. **Clone the repository**

```bash
git clone <your-repo-url>
cd Ai_based_cheating_detector
```

2. **Create virtual environment**

```bash
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Download models** (YOLO will auto-download on first run)

```bash
# MediaPipe model will auto-download
# For text detection, you need to train the model first (see below)
```

### Running the Application

```bash
cd backend
python app.py
```

Open browser: `http://127.0.0.1:5000`

## 📁 Project Structure

```
Ai_based_cheating_detector/
├── backend/
│   ├── app.py                    # Main Flask application (FIXED)
│   ├── ai_integrator.py          # AI model integration (FIXED)
│   ├── camera_manager.py         # Camera operations (FIXED)
│   ├── config.py                 # Configuration
│   ├── integrity_handler.py      # Integrity auditing
│   └── utils/
│       ├── file_utils.py         # File operations (FIXED)
│       ├── logging_utils.py      # Logging
│       ├── response_utils.py     # API responses
│       └── risk_calculator.py    # Unified risk scoring (NEW)
├── integrity_auditor/
│   ├── text_auditor.py          # AI text detection
│   ├── code_auditor.py          # Code plagiarism
│   ├── stylometry.py            # Writing style analysis
│   ├── datasets.py              # Dataset management
│   └── utils.py                 # Utilities
├── src/
│   ├── gaze_module.py           # Gaze tracking (FIXED)
│   ├── object_module.py         # Object detection (FIXED)
│   └── integrator.py            # Vision Guardian (FIXED)
├── static/
│   ├── css/
│   │   ├── main.css
│   │   ├── components.css
│   │   └── responsive.css       # (FIXED - No duplicates)
│   └── js/
│       ├── api.js
│       ├── main.js
│       ├── ui.js
│       ├── utils.js
│       └── components/
│           ├── analytics.js
│           ├── footer.js
│           ├── header.js
│           ├── notification.js   # (FIXED filename)
│           └── video.js
├── templates/
│   └── index.html               # Main page (FIXED)
├── models/                      # AI models directory
├── requirements.txt             # (FIXED - Complete)
└── README.md                    # This file
```

## 🔧 Configuration

Edit `backend/config.py`:

```python
# AI Configuration
AI_CONFIG = {
    'enable_yolo': True,
    'enable_gaze': True,
    'max_students': 1,
    'frame_skip': 2,
    'target_fps': 15
}

# Security Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_TEXT_LENGTH = 50000
```

## 🎯 Training Models

### Text AI Detection Model

```bash
# Navigate to integrity_auditor
cd integrity_auditor

# Create training script (example)
python -c "
from text_auditor import TextAuditor
from datasets import DatasetManager

# Load dataset
dm = DatasetManager()
texts, labels = dm.load_hc3_dataset(sample_size=1000)

# Train model (implement your training logic)
# Save to models/ai_detector/
"
```

### Stylometry Model

```bash
# Collect writing samples from different authors
# Train and save to models/stylometry_model.pkl
```

## 🐛 Known Issues & Fixes

### All Critical Issues Fixed ✅

1. ✅ Import typo (`untils` → `utils`)
2. ✅ Duplicate application in index.html
3. ✅ Thread safety in camera manager
4. ✅ No dummy data - real errors reported
5. ✅ Unified risk scoring system
6. ✅ Secure file uploads with validation
7. ✅ Fixed gaze tracking normalization
8. ✅ Memory leaks fixed (bounded collections)
9. ✅ Proper cleanup and resource management
10. ✅ Missing files added

## 📊 API Endpoints

### Proctoring

- `POST /api/start_proctoring` - Start monitoring
- `POST /api/stop_proctoring` - Stop monitoring
- `GET /api/proctoring_results` - Get current results
- `POST /api/take_screenshot` - Capture screenshot
- `GET /video_feed` - Live video stream

### Integrity Auditing

- `POST /api/analyze_text` - Analyze text for AI
- `POST /api/check_code_plagiarism` - Check code similarity
- `POST /api/compare_code_files` - Compare uploaded files

### System

- `GET /api/system_status` - System status
- `GET /api/debug_detection` - Debug detections

## 🔒 Security Features

- File size validation (10MB limit)
- File type validation (whitelist)
- Filename sanitization (prevents path traversal)
- Input length validation
- Secure temporary file handling
- Automatic cleanup
- Thread-safe operations

## 🎨 Frontend Features

- Modular component system
- Real-time updates
- Responsive design
- Toast notifications
- Modal dialogs
- Risk assessment visualization

## 📝 Usage Example

```javascript
// Start proctoring
const api = new APIHandler();
await api.startProctoring(0);

// Get results
const results = await api.getProctoringResults();
console.log("Risk Score:", results.risk_score);

// Stop proctoring
await api.stopProctoring();
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

- YOLOv8 by Ultralytics
- MediaPipe by Google
- Transformers by Hugging Face
- Flask framework

## 📞 Support

For issues and questions:

- Create an issue on GitHub
- Email: [your-email]

## 🔄 Changelog

### Version 2.0 (Fixed)

- ✅ Fixed all critical bugs
- ✅ Added security features
- ✅ Improved memory management
- ✅ Fixed gaze tracking math
- ✅ Unified risk scoring
- ✅ No dummy data
- ✅ Thread-safe operations

### Version 1.0 (Original)

- Initial release with bugs
