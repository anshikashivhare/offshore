from pptx import Presentation
from pptx.util import Inches

def create_presentation():
    prs = Presentation()
    
    # Slide 1: Title
    slide_layout = prs.slide_layouts[0] # title slide
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = "AI-Enabled Antarctic Sea-Ice, Iceberg Trajectory, and Navigation Decision Support System"
    subtitle.text = "SIH PS 26059\nArchitecture: Frozen | Data: Synthetic/Demo"

    # Slide 2: Problem
    slide_layout = prs.slide_layouts[1]
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = "The Problem"
    slide.placeholders[1].text = "Antarctic maritime navigation is affected by dynamic hazards:\n- Sea ice, icebergs, wind, waves, ocean currents.\n\nThe shortest route ≠ necessarily lowest-risk route.\nEnvironmental information is distributed and siloed."

    # Slide 3: Proposed Solution
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = "Proposed Solution"
    slide.placeholders[1].text = "Route Request\n↓\nEnvironmental + ML Data\n↓\nRisk / Navigability\n↓\nTime-aware A*\n↓\nRoute Validation\n↓\nDecision-support output"

    # Slide 4: System Architecture
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = "System Architecture"
    slide.placeholders[1].text = "1. Prediction: XGBoost (Sea Ice) + LSTM (Icebergs)\n2. Risk Interpretation: Composite Risk Engine (max)\n3. Hard Constraints: Route Validator\n4. Optimization: 4D Time-Aware A*\n5. Visualization: React + GeoJSON"

    # Slide 5: Sea-Ice ML
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = "Sea-Ice ML (XGBoost v002)"
    slide.placeholders[1].text = "Purpose: Predicts sea-ice spatial concentration grids.\nIntegration: Penalizes the A* grid dynamically.\nProvenance: Trained on synthetic simulated environment data."

    # Slide 6: Iceberg LSTM
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = "Iceberg Trajectory ML (LSTM v002)"
    slide.placeholders[1].text = "Architecture: 2-layer LSTM\nEvaluation: T+3h prediction horizon.\nSplits: 22 train / 4 validation / 4 test icebergs.\nSolution: Uses wrapped longitude displacement to safely cross the antimeridian."

    # Slide 7: Causal Integration Evidence
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = "From Prediction to Risk to Routing"
    slide.placeholders[1].text = "LSTM prediction → predicted position → CPA calculation → encounter-risk index → A* edge cost.\n\nMetrics:\nLSTM v002 Mean Haversine Error = 0.27 km (Held-out synthetic test-set result).\nThis is an empirical summary, not a collision probability."

    # Slide 8: Safety Fallback
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = "Live Safety Architecture"
    slide.placeholders[1].text = "When required risk data is unavailable, a 'Safest' objective request fails closed.\nThe backend returns a 400 Bad Request.\nWe do not hallucinate zero-risk routes."

    # Slide 9: Limitations
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = "Scientific Limitations"
    slide.placeholders[1].text = "- Synthetic training/evaluation data\n- 3-hour validated iceberg horizon\n- Unverified PostgreSQL persistence (Fallback to DEMO_MODE)\n- Non-certified navigation use"

    # Slide 10: Closing
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = "Closing"
    slide.placeholders[1].text = "This is an AI-assisted, geospatial, risk-aware navigation decision-support prototype.\nThe mathematical causality has been proven; the system is ready for real-world telemetry."

    prs.save('SIH_26059_Final_Presentation.pptx')
    print("Presentation saved.")

if __name__ == '__main__':
    create_presentation()
