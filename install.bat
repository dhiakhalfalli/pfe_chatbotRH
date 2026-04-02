@echo off
REM ─── Install all dependencies ─────────────────────────────────────────────────
echo.
echo [92m Installing HR Platform Dependencies [0m
echo ─────────────────────────────────────────────────────────────────

REM Python packages
echo [96m Installing Python packages (minimal)...[0m
pip install fastapi uvicorn[standard] python-multipart pydantic pydantic-settings requests python-dotenv PyMuPDF pypdf

REM Try installing optional heavy deps
echo [96m Installing optional ML packages (will skip if no GPU memory)...[0m
pip install spacy easyocr motor pymongo

REM spaCy model
echo [96m Downloading spaCy model...[0m
python -m spacy download en_core_web_sm

REM LangGraph / LangChain
echo [96m Installing LangChain/LangGraph...[0m
pip install langchain langchain-core langchain-community langgraph

REM Frontend
echo [96m Installing Node.js packages...[0m
cd frontend
npm install
cd ..

echo.
echo [92m ✅ Installation complete! Run start.bat to launch the platform.[0m
pause
