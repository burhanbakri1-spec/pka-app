import os
import io
import json
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from PIL import Image, ImageDraw, ImageFont
import qrcode

# --- Path Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
OUTPUT_DIR = os.path.join(BASE_DIR, "Output_Cards")

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_template_path(role):
    """Determines the correct .docx template path based on the member's role."""
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

def get_static_preview_image(role):
    """
    Looks for a static preview image for the given role in the assets folder.
    Returns a PIL Image object. If not found, returns a gray placeholder.
    """
    for ext in ['.jpg', '.png', '.jpeg']:
        preview_path = os.path.join(ASSETS_DIR, f"template_{role.lower()}{ext}")
        if os.path.exists(preview_path):
            return Image.open(preview_path)

    # If no preview image is found, create a placeholder
    img = Image.new('RGB', (530, 340), color='#D3D3D3')
    d = ImageDraw.Draw(img)
    try:
        # Use a common font if available, otherwise default
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font = ImageFont.load_default()
    d.text((10,10), f"No preview available for '{role}' role.\n(Looking for template_{role.lower()}.jpg)", fill=(0,0,0), font=font)
    return img

def generate_card_image(member_data):
    """
    Generates a member ID card using a Word template.

    Args:
        member_data (dict): A dictionary containing the member's information.

    Returns:
        tuple: A tuple containing (path_to_docx_file, preview_image_object).
    """
    try:
        role = member_data.get('role', 'Player')
        template_path = get_template_path(role)
        doc = DocxTemplate(template_path)
        
        specific_data = json.loads(member_data.get('specific_data', '{}'))

        # --- General Information ---
        context = {
            'name_ar': member_data.get('full_name_ar', ''),
            'name_en': member_data.get('full_name', ''),
            'pkf_id': member_data.get('pkf_id', ''),
            'role': member_data.get('role', ''),
            'dob': member_data.get('dob', ''),
            'club': member_data.get('club_name', ''),
            'belt': member_data.get('current_belt', ''),
            'belt_date': specific_data.get('current_belt_date', ''), # Assuming this might be in specific_data
        }

        # --- Photo ---
        photo_path = member_data.get('photo_path')
        if photo_path and os.path.exists(photo_path):
            context['photo'] = InlineImage(doc, photo_path, width=Mm(22), height=Mm(28))
        else:
            placeholder_path = os.path.join(ASSETS_DIR, 'placeholder.jpg')
            if os.path.exists(placeholder_path):
                context['photo'] = InlineImage(doc, placeholder_path, width=Mm(22), height=Mm(28))

        # --- QR Code ---
        qr_data = f"Name: {context['name_en']}\nID: {context['pkf_id']}\nRole: {context['role']}"
        qr_img = qrcode.make(qr_data)
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        context['qr'] = InlineImage(doc, qr_buffer, width=Mm(20))

        # --- Player Specific ---
        if role == 'Player':
            context.update({
                'weight': specific_data.get('weight', ''),
                'rank_loc': specific_data.get('nat_rank', ''),
                'rank_intl': specific_data.get('int_rank', ''),
                'x_kata': 'X' if specific_data.get('kata_check') else '',
                'x_kumite': 'X' if specific_data.get('kumite_check') else '',
            })

        # --- Coach Specific ---
        elif role == 'Coach':
            context.update({
                'coach_nat': specific_data.get('coach_national_degree', ''),
                'coach_intl': specific_data.get('coach_international_degree', ''),
                'coach_asia': specific_data.get('coach_asian_degree', ''),
            })

        # --- Referee Specific ---
        elif role == 'Referee':
            # A more robust way to find the highest degree mentioned
            def get_highest_degree(data, discipline):
                keys = [f'ref_{discipline}_{level}_degree' for level in ['international', 'asian', 'national']]
                for key in keys:
                    if data.get(key):
                        return data[key]
                return 'N/A'
            context['ref_kumite_rb'] = get_highest_degree(specific_data, 'kumite')
            context['ref_kata_ja'] = get_highest_degree(specific_data, 'kata')
            context['license_date'] = member_data.get('expiry_date', '')

        # --- Admin Specific ---
        elif role == 'Admin':
            context['admin_title'] = member_data.get('admin_title', specific_data.get('admin_title', ''))

        # Render the document
        doc.render(context)

        # Save the generated .docx file
        safe_pkf_id = "".join(c for c in context['pkf_id'] if c.isalnum()).rstrip()
        output_filename = f"Card_{context['name_en'].replace(' ', '_')}_{safe_pkf_id}.docx"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        doc.save(output_path)

        # Get the static preview image for the UI
        preview_image = get_static_preview_image(role)
        
        return output_path, preview_image

    except Exception as e:
        import traceback
        traceback.print_exc()
        # In case of an error, return None for both values
        return None, None