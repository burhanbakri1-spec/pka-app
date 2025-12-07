import os
import io
import json
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from PIL import Image
import qrcode

# --- Path Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Ensure the temporary output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_template_path(role):
    """Determines the correct .docx template path based on the member's role."""
    # The user mentioned 'template_aplayer.docx', which is likely a typo.
    # We will check for 'template_player.docx' first, then the typo as a fallback.
    if role == 'Player':
        player_template_path = os.path.join(ASSETS_DIR, 'template_player.docx')
        aplayer_template_path = os.path.join(ASSETS_DIR, 'template_aplayer.docx')
        if os.path.exists(player_template_path):
            return player_template_path
        elif os.path.exists(aplayer_template_path):
            print("INFO: Using 'template_aplayer.docx'. It is recommended to rename it to 'template_player.docx'.")
            return aplayer_template_path
        else:
            raise FileNotFoundError("Template for Player not found. Neither 'template_player.docx' nor 'template_aplayer.docx' exists in assets folder.")

    role_map = {
        'Coach': 'template_coach.docx',
        'Referee': 'template_referee.docx',
        'Admin': 'template_admin.docx'
    }
    filename = role_map.get(role)
    if not filename:
        raise ValueError(f"No template defined for role: {role}")

    path = os.path.join(ASSETS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Template file not found: {path}")
    return path

def generate_member_card(member_data):
    """Generates a member ID card using a Word template and returns the path to the temporary file."""
    role = member_data.get('role', 'Player')
    template_path = get_template_path(role)
    doc = DocxTemplate(template_path)

    specific_data = json.loads(member_data.get('specific_data', '{}'))

    # --- General Information ---
    context = {
        'name_ar': member_data.get('full_name_ar', ''),
        'name_en': member_data.get('full_name', ''),
        'pkf_id': member_data.get('pkf_id', ''),
        'dob': member_data.get('dob', ''),
        'club': member_data.get('club_name', ''),
    }

    # --- Photo ---
    photo_path = member_data.get('photo_path')
    if photo_path and os.path.exists(photo_path):
        context['photo'] = InlineImage(doc, photo_path, width=Mm(19), height=Mm(24))
    else:
        placeholder_path = os.path.join(ASSETS_DIR, 'placeholder.jpg')
        if os.path.exists(placeholder_path):
            context['photo'] = InlineImage(doc, placeholder_path, width=Mm(19), height=Mm(24))

    # --- Player Specific ---
    if role == 'Player':
        context.update({
            'weight': specific_data.get('weight', ''),
            'rank_loc': specific_data.get('nat_rank', ''),
            'rank_intl': specific_data.get('int_rank', ''),
            'belt': member_data.get('current_belt', ''),
            'belt_date': member_data.get('current_belt_date', ''),
        })

    # --- Coach Specific ---
    if role == 'Coach':
        context.update({
            'coach_nat': specific_data.get('coach_national_degree', ''),
            'coach_intl': specific_data.get('coach_international_degree', ''),
            'coach_asia': specific_data.get('coach_asian_degree', ''),
        })

    # --- Referee Specific ---
    if role == 'Referee':
        kumite_degrees = [specific_data.get(k) for k in specific_data if 'kumite' in k and 'degree' in k]
        kata_degrees = [specific_data.get(k) for k in specific_data if 'kata' in k and 'degree' in k]
        context['ref_kumite_rb'] = next((d for d in kumite_degrees if d), 'N/A')
        context['ref_kata_ja'] = next((d for d in kata_degrees if d), 'N/A')
        context['license_date'] = member_data.get('expiry_date', '')

    # --- Admin Specific ---
    if role == 'Admin':
        context['admin_title'] = member_data.get('admin_title', specific_data.get('admin_title', ''))

    # Render the document
    doc.render(context)

    # Save to a temporary file
    safe_pkf_id = "".join(c for c in context['pkf_id'] if c.isalnum()).rstrip()
    temp_filename = f"card_{safe_pkf_id}_{role.lower()}.docx"
    temp_path = os.path.join(OUTPUT_DIR, temp_filename)
    doc.save(temp_path)

    return temp_path
