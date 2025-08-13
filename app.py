import gradio as gr
import torch
import numpy as np
import openai
import os
import json
import easyocr
from PIL import Image
import streamlit as st

# Try to get from Streamlit secrets
if "OPENAI_API_KEY" in st.secrets:
    openai_key = st.secrets["OPENAI_API_KEY"]
else:
    # Fallback to environment variable
    openai_key = os.getenv("OPENAI_API_KEY", "")

if not openai_key:
    st.error("Missing OpenAI API key. Please set it in Streamlit secrets or as an environment variable.")
else:
    os.environ["OPENAI_API_KEY"] = openai_key

# Use /tmp for writable storage in Streamlit Cloud
model_dir = os.path.join("/tmp", ".EasyOCR")
os.makedirs(model_dir, exist_ok=True)

reader = easyocr.Reader(
    ['en'],
    model_storage_directory=model_dir,
    user_network_directory=os.path.join(model_dir, "user_network")
)


def extract_ui_elements(screen):
    """Detect UI elements using EasyOCR (Tesseract Alternative)."""
    if screen is None or isinstance(screen, str) or (isinstance(screen, np.ndarray) and screen.size == 0):  # Handle empty input cases
        return []
    
    result = reader.readtext(np.array(screen))
    
    detected_ui = []
    for (bbox, text, conf) in result:
        if conf > 0.5:  # Confidence threshold to filter out low-quality detections
            detected_ui.append({"component": text, "bounding_box": bbox})

    return detected_ui

def generate_ui_data_model(user_story, summary, screen=None):
    """Generates a UI Data Model using detected UI elements or assumptions from user input."""
    if screen is None or isinstance(screen, str) or (isinstance(screen, np.ndarray) and screen.size == 0):  # Handle missing or empty image input
        detected_ui_elements = []
    else:
        detected_ui_elements = extract_ui_elements(screen)
    
    if not detected_ui_elements:
        detected_ui_elements = "No UI elements detected from the image. Generating UI data model based on provided user story and summary."
    
    prompt = f"""
    You are a Business System Analyst creating a **UI Data Model** for developers.
    Below are the provided inputs:
    - **User Story**: {user_story if user_story else "No user story provided."}
    - **Summary/Description**: {summary if summary else "No additional summary provided."}
    - **Detected UI Elements (if available)**: {detected_ui_elements}

    Generate a **JSON UI Data Model** ensuring:
    - **Consistency** in naming UI components.
    - **Hierarchy** with sections, buttons, inputs, icons, etc.
    - **Clean JSON formatting**.

    Follow this JSON structure:
    {{
        {{
            <ui-data-model> 
            "sectionOne": 
            {{ 
            "fieldOne":<URI>, // e.g. Icon location for fieldOne which is an icon 
            "fieldTwo": <STRING>, // e.g. String text for fieldTwo 
            "fieldThree": <STRING>, // e.g. String text for fieldThree 
            "fieldFour": <STRING>, // e.g. String text for fieldFour "sectionTwo":  
            {{
            "fieldOne":<URI>, // e.g. Icon location for fieldOne which is an icon 
            "fieldTwo": <STRING>, // e.g. String text for fieldTwo 
            "fieldThree": <STRING>, // e.g. String text for fieldThree 
            "fieldFour": <dropdown>, // e.g. String text for fieldFour 
                {{ 
                "dropDownOption1": <text>, 
                "dropDownOption2": <text>, 
                "dropDownOption3": <text>, 
                }}, 
                
            }}, 
        }} </ui-data-model> </TEMPLATE 1>
        }}
    }}

    Now, generate the UI Data Model in JSON format.
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are an AI assistant trained to generate standardized UI Data Models."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except openai.OpenAIError as e:
        return json.dumps({"error": f"OpenAI API error: {str(e)}"}, indent=4)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {str(e)}"}, indent=4)

def generate_gherkin_from_ui(ui_data_model, user_story, summary):
    """Generates structured Gherkin user stories from the UI data model."""

    prompt = f"""
    You are an AI assistant trained to generate **structured Gherkin user stories**.
    
    Below are the provided inputs:
    - **User Story**: {user_story if user_story else "No user story provided."}
    - **Summary/Description**: {summary if summary else "No additional summary provided."}
    - **UI Data Model**: {ui_data_model}

    ### Instructions:
    1. **Generate structured Gherkin user stories** based on the inputs.
    2. Each UI element should have an **associated user interaction**.
    3. Include **positive & negative scenarios**.
    4. Provide **expected results** for each action.
    5. Additionally, generate **non-functional user stories**, including:
       - **Performance**
       - **Security**
       - **Usability**
       - **Accessibility**

    Now, generate structured and consistent Gherkin scenarios.
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are an AI assistant trained to generate structured Gherkin user stories."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except openai.OpenAIError as e:
        return json.dumps({"error": f"OpenAI API error: {str(e)}"}, indent=4)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {str(e)}"}, indent=4)

def generate_test_cases(gherkin_story, platform, technology):
    """Generates structured imperative and non-functional test cases for automation testing, ensuring consistency."""
    
    prompt = f"""
    Given the following user story:
    {gherkin_story}
    
    Generate **structured imperative test cases** suitable for **automation testing**.
    - Target Platform: {platform}
    - Recommended Technology: {technology}
    - Include proper test steps, assertions, and expected results.
    - Ensure test cases follow a structured format.
    - Include all possible scenarios, covering edge cases.
    - Additionally, generate relevant **non-functional test cases**, including:
      - **Performance**
      - **Security**
      - **Usability**
      - **Accessibility**
      - Verify that all UI elements have appropriate **color contrast ratios**.
      - Ensure all images/icons have **alt text** for screen readers.
      - Validate that text elements are readable against different backgrounds.
      - Check that keyboard navigation works seamlessly across UI components.
      - Test using accessibility tools such as Axe or Lighthouse.

    Now, generate structured imperative and non-functional test cases.
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are an AI assistant trained to generate structured imperative and non-functional test cases for automation."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except openai.OpenAIError as e:
        return json.dumps({"error": f"OpenAI API error: {str(e)}"}, indent=4)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {str(e)}"}, indent=4)


def generate_feature_file(test_cases, platform, step_definition_format):
    if not platform:
        platform = "Web"  # Default value if platform is not selected
    
    """Generates a structured Gherkin feature file with platform-specific step definitions."""
    
    prompt = f"""
    Given the following structured imperative test cases:
    {test_cases}
    
    Follow this feature file template:
       Feature: [Feature Name]

        Scenario: [Scenario Name]
          Given [Precondition]
          When [Action]
          Then [Expected Outcome]

        @platform-specific
        Scenario: [Platform-Specific Scenario]
          Given [Precondition]
          When [Platform-specific Action]
          Then [Expected Outcome]
    Ensure step definitions match the selected platform: {platform}.
    - Use step definitions in the selected format: {step_definition_format}.
    - Provide structured Given-When-Then steps specific to the format.
    - Include **test data** where applicable for input fields.
    - Ensure alt text is validated for image-based UI elements.
    - Validate expected color contrast ratios in assertions.
    Now, generate the feature file with correct step definitions for the selected platform: {platform}.
    
    - Ensure step definitions include **preconditions**, **actions**, and **expected outcomes**.
    - Provide **clear assertions** for UI elements and business logic.
    - Include **test data** where applicable for better test coverage.
    - Ensure all **accessibility** checks (color contrast, alt text) are validated.
    - Differentiate **Web vs. Mobile step definitions** where necessary.
    - Use structured Gherkin syntax with meaningful step descriptions.
    - Generate **step definitions in Python (Behave), Java (Cucumber), or JS (Cypress)** for automation purposes.
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are an AI assistant trained to generate structured feature files with step definitions."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except openai.OpenAIError as e:
        return json.dumps({"error": f"OpenAI API error: {str(e)}"}, indent=4)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {str(e)}"}, indent=4)

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("## UI Data Model, Gherkin Story, and Test Case Generator")
    
    user_story_input = gr.Textbox(label="Enter User Story", lines=5)
    summary_input = gr.Textbox(label="Enter Additional Summary or Description", lines=5)
    screen_input = gr.Image(type="pil", label="Upload UI Screenshot (Optional)")
    
    platform_input = gr.Dropdown(label="Select Platform", choices=["Web", "Mobile"], type="value")
    technology_input = gr.Dropdown(label="Select Recommended Technology", choices=["Selenium", "Cypress", "Appium", "Detox"], type="value")
    
    ui_data_model_output = gr.Textbox(label="Generated UI Data Model (JSON)", lines=15, interactive=True)
    gherkin_output = gr.Textbox(label="Generated Gherkin User Stories", lines=10, interactive=True)
    test_case_output = gr.Textbox(label="Generated Imperative & Non-Functional Test Cases", lines=15, interactive=True)
    feature_file_output = gr.Textbox(label="Generated Feature File", lines=15, interactive=True)
    
    step_definition_input = gr.Dropdown(
        label="Select Step Definition Format",
        choices=["Python (Behave)", "Java (Cucumber)", "JavaScript (Cypress)"],
        type="value"
    )

    with gr.Row():
        generate_ui_btn = gr.Button("Generate UI Data Model")
        generate_gherkin_btn = gr.Button("Generate Gherkin Story")
        generate_test_cases_btn = gr.Button("Generate Test Cases")
        generate_feature_file_btn = gr.Button("Generate Feature File")

    
    generate_ui_btn.click(generate_ui_data_model, inputs=[user_story_input, summary_input, screen_input], outputs=ui_data_model_output)
    generate_gherkin_btn.click(generate_gherkin_from_ui, inputs=ui_data_model_output, outputs=gherkin_output)
    generate_test_cases_btn.click(generate_test_cases, inputs=[gherkin_output, platform_input, technology_input], outputs=test_case_output)
    generate_feature_file_btn.click(generate_feature_file, inputs=[test_case_output, platform_input, step_definition_input], outputs=feature_file_output)

demo.launch(share=True)
