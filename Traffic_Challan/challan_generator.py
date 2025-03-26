import streamlit as st
from PIL import Image
import google.generativeai as genai
import os
from fpdf import FPDF
from datetime import datetime

# Configure Google Gemini API
genai.configure(api_key="AIzaSyCNyOZ4YRqgLf5b6N7q15hWVTUwqXU3bEE")
model = genai.GenerativeModel('gemini-1.5-flash')

# Streamlit App Configuration
st.set_page_config(
    page_title="AI Traffic Challan System",
    page_icon="👮",
    layout="wide"
)

# Sidebar
st.sidebar.title("🚨 Traffic Enforcement System")
st.sidebar.markdown("""
**🔍 AI-Powered Features:**
- License Plate Recognition
- Violation Detection
- Automatic Fine Calculation
- Digital Challan Generation
""")
st.sidebar.markdown("---")
st.sidebar.markdown("Developed by **Rupesh Khobragade**")

# Main App
st.title("👮 AI Traffic Challan Generator")
st.markdown("Automated traffic violation detection and enforcement system")

# Violation Database (changed ₹ to Rs.)
VIOLATIONS = {
    "Not wearing helmet": "Rs. 500",
    #"Red light violation": "Rs. 500",
    "No registration": "Rs. 5000",
    "No driving license": "Rs. 5000",
    #"Drunk driving": "Rs. 10000",
    #"Over-speeding": "Rs. 1000",
    #"Dangerous driving": "Rs. 5000",
    "No insurance": "Rs. 2000",
    #"Triple riding": "Rs. 1000",
    "Illegal parking": "Rs. 400",
    "Vehicle modification": "Rs. 3000",
    "Mobile phone usage": "Rs. 1000",
    "No pollution certificate": "Rs. 2000"
}

# Session State Initialization
if 'vehicle_number' not in st.session_state:
    st.session_state.vehicle_number = ""
if 'suggested_violations' not in st.session_state:
    st.session_state.suggested_violations = []

# Tab Interface
tab1, tab2 = st.tabs(["📸 AI Detection Mode", "📝 Manual Entry Mode"])

def detect_license_plate(image):
    """Extract license plate number using Gemini"""
    try:
        response = model.generate_content([
            "Extract the vehicle license plate number from this traffic image. "
            "Return ONLY the alphanumeric characters in Indian format (e.g. MH02AB1234). "
            "Ignore any other text or analysis.",
            image
        ])
        return response.text.strip()
    except Exception as e:
        st.error(f"Plate detection failed: {str(e)}")
        return ""

def detect_traffic_violations(image):
    """Identify potential violations from image"""
    try:
        response = model.generate_content([
            "Analyze this traffic image and identify any violations from this list:\n" + 
            "\n".join(VIOLATIONS.keys()) + 
            "\n\nReturn ONLY comma-separated violation names that are clearly visible. "
            "Do not invent new violations.",
            image
        ])
        detected = [v.strip() for v in response.text.split(",") 
                   if v.strip() in VIOLATIONS]
        return detected[:3]  # Return max 3 most obvious violations
    except Exception as e:
        st.error(f"Violation analysis error: {str(e)}")
        return []

def generate_challan_pdf(vehicle_number, violations):
    """Generate professional PDF challan"""
    pdf = FPDF()
    pdf.add_page()
    
    try:
        # Try to use DejaVu font if available
        pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        pdf.add_font('DejaVu', 'B', 'DejaVuSansCondensed-Bold.ttf', uni=True)
        pdf.add_font('DejaVu', 'I', 'DejaVuSansCondensed-Oblique.ttf', uni=True)
        font_family = 'DejaVu'
    except:
        # Fallback to built-in font if DejaVu not available
        font_family = 'helvetica'
        st.warning("DejaVu font not found - using system font instead")
    
    # Header
    pdf.set_font(font_family, 'B', 16)
    pdf.cell(0, 10, 'OFFICIAL TRAFFIC CHALLAN', 0, 1, 'C')
    pdf.ln(10)
    
    # Vehicle Info
    pdf.set_font(font_family, '', 12)
    pdf.cell(0, 10, f'Vehicle Number: {vehicle_number}', 0, 1)
    pdf.cell(0, 10, f'Date: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}', 0, 1)
    pdf.ln(5)
    
    # Violations Table
    pdf.set_font(font_family, 'B', 12)
    pdf.cell(120, 10, 'Violation', 1)
    pdf.cell(30, 10, 'Fine', 1, 1)
    
    pdf.set_font(font_family, '', 12)
    total_fine = 0
    for violation in violations:
        fine_str = VIOLATIONS[violation]
        # Extract numeric value from "Rs. 500" format
        fine_value = int(fine_str.replace("Rs. ", "").strip())
        pdf.cell(120, 10, violation, 1)
        pdf.cell(30, 10, fine_str, 1, 1)
        total_fine += fine_value
    
    # Total Fine
    pdf.set_font(font_family, 'B', 12)
    pdf.cell(120, 10, 'TOTAL FINE', 1)
    pdf.cell(30, 10, f"Rs. {total_fine}", 1, 1)
    
    # Footer
    pdf.ln(15)
    pdf.set_font(font_family, 'I', 10)
    pdf.multi_cell(0, 5, 
        "Payment Instructions:\n"
        "1. Pay online at transportdepartment.gov.in\n"
        "2. Visit any traffic police station within 15 days\n"
        "3. Late payments attract 10% additional penalty")
    
    return pdf, total_fine

# AI Detection Tab
with tab1:
    st.header("📸 AI-Powered Violation Detection")
    uploaded_file = st.file_uploader(
        "Upload traffic violation image", 
        type=["jpg", "jpeg", "png"],
        help="Clear images of vehicles or traffic scenes work best"
    )
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Traffic Image", use_column_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚗 Detect License Plate", help="Extract vehicle registration number"):
                with st.spinner("Scanning license plate..."):
                    plate_number = detect_license_plate(image)
                    if plate_number:
                        st.session_state.vehicle_number = plate_number
                        st.success(f"Detected: {plate_number}")
        
        with col2:
            if st.button("🚨 Detect Violations", help="Identify traffic violations"):
                with st.spinner("Analyzing image for violations..."):
                    violations = detect_traffic_violations(image)
                    if violations:
                        st.session_state.suggested_violations = violations
                        st.success("Potential violations detected!")
                        for v in violations:
                            st.write(f"• {v} ({VIOLATIONS[v]})")
                    else:
                        st.warning("No clear violations detected")

# Manual Entry Tab
with tab2:
    st.header("📝 Manual Information Entry")
    vehicle_number = st.text_input(
        "Vehicle Registration Number",
        value=st.session_state.get('vehicle_number', ''),
        placeholder="e.g. MH02AB1234"
    )

# Violation Selection
if vehicle_number:
    st.divider()
    st.subheader("⛔ Select Violations")
    
    suggested = st.session_state.get('suggested_violations', [])
    selected_violations = []
    
    cols = st.columns(2)
    for i, violation in enumerate(VIOLATIONS.keys()):
        with cols[i % 2]:
            default = violation in suggested
            if st.checkbox(
                f"{violation} ({VIOLATIONS[violation]})", 
                value=default,
                key=f"violation_{i}"
            ):
                selected_violations.append(violation)
    
    if selected_violations:
        total = sum(int(VIOLATIONS[v].replace("Rs. ", "")) for v in selected_violations)
        st.markdown(f"### Total Fine: Rs. {total}")
        
        if st.button("📄 Generate Challan", type="primary"):
            with st.spinner("Generating official challan..."):
                try:
                    pdf, total_fine = generate_challan_pdf(
                        vehicle_number, 
                        selected_violations
                    )
                    
                    filename = f"Challan_{vehicle_number}_{datetime.now().strftime('%Y%m%d')}.pdf"
                    pdf.output(filename)
                    
                    with open(filename, "rb") as f:
                        st.download_button(
                            "⬇️ Download Challan",
                            f,
                            file_name=filename,
                            mime="application/pdf"
                        )
                    st.success("Challan generated successfully!")
                    os.remove(filename)
                except Exception as e:
                    st.error(f"Challan generation failed: {str(e)}")
    else:
        st.warning("Please select at least one violation")
else:
    st.info("Please upload an image or enter vehicle number to begin")

# Footer
st.markdown("---")
st.caption("Note: This is a demonstration system. Generated challans are not legally binding.")