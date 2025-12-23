#!/bin/bash
# Run the CRM Message Generation Streamlit App

cd "$(dirname "$0")"

echo "=============================================="
echo "  CRM 메시지 자동 생성 시스템"
echo "  Amorepacific AI Innovation Challenge"
echo "=============================================="
echo ""
echo "Starting Streamlit server..."
echo "Access the app at: http://localhost:8501"
echo ""

streamlit run ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
