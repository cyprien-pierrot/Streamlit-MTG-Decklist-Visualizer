import streamlit as st
import requests
import re
import time

# App title
st.title("Decklist Visualizer")

decklist = st.text_area(
    "Enter your decklist:",
    height=300,
    placeholder="Paste your decklist here...",
    key="decklist_input"
)

def split_decklist(decklist_text):
    maindeck_lines = []
    sideboard_lines = []
    current = "main"
    for line in decklist_text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.lower() == "deck":
            current = "main"
            continue
        if line.lower() == "sideboard":
            current = "side"
            continue
        if current == "main":
            maindeck_lines.append(line)
        else:
            sideboard_lines.append(line)
    return maindeck_lines, sideboard_lines

def parse_card_entries(lines):
    entries = []
    for line in lines:
        match = re.match(r"(\d+)\s+(.+)", line)
        if match:
            count = int(match.group(1))
            card_name = match.group(2)
            entries.append((card_name, count))
    return entries

def get_card_data(card_name):
    api_url = f"https://api.scryfall.com/cards/named?exact={card_name}"
    resp = requests.get(api_url)
    if resp.status_code == 200:
        return resp.json()
    return None

def get_card_image_url(card_data):
    if not card_data:
        return None
    if 'image_uris' in card_data:
        return card_data['image_uris'].get('normal')
    elif 'card_faces' in card_data:
        return card_data['card_faces'][0]['image_uris'].get('normal')
    return None

def is_land(card_data):
    return card_data and 'type_line' in card_data and 'Land' in card_data['type_line']

def display_card_grid(card_list, n_cols=5):
    for i in range(0, len(card_list), n_cols):
        row = card_list[i:i+n_cols]
        cols = st.columns(n_cols)
        for col, card in zip(cols, row):
            card_name, count, card_data = card
            img_url = get_card_image_url(card_data)
            if img_url:
                col.image(img_url, caption=f"{count}x {card_name}", use_container_width=True)
            else:
                col.warning(f"Image not found for '{card_name}'")
        # Fill any remaining columns in the row with empty
        for j in range(len(row), n_cols):
            cols[j].empty()

if decklist:
    maindeck_lines, sideboard_lines = split_decklist(decklist)
    maindeck_entries = parse_card_entries(maindeck_lines)
    sideboard_entries = parse_card_entries(sideboard_lines)

    # Remove duplicates (sum quantities)
    def combine_entries(entries):
        card_dict = {}
        for name, count in entries:
            card_dict[name] = card_dict.get(name, 0) + count
        return list(card_dict.items())
    maindeck_entries = combine_entries(maindeck_entries)
    sideboard_entries = combine_entries(sideboard_entries)

    # Categorize maindeck into spells and lands
    lands = []
    spells = []
    for card_name, count in maindeck_entries:
        card_data = get_card_data(card_name)
        time.sleep(0.1)
        if is_land(card_data):
            lands.append((card_name, count, card_data))
        else:
            spells.append((card_name, count, card_data))

    st.header("Maindeck")

    # Spells first, with count
    if spells:
        total_spells = sum(count for _, count, _ in spells)
        st.subheader(f"Spells ({total_spells})")
        display_card_grid(spells, n_cols=5)

    # Then lands, with count
    if lands:
        total_lands = sum(count for _, count, _ in lands)
        st.subheader(f"Lands ({total_lands})")
        display_card_grid(lands, n_cols=5)

    # Sideboard
    if sideboard_entries:
        st.header("Sideboard")
        # Fetch card_data for sideboard cards if not already done
        sideboard_with_data = []
        for card_name, count in sideboard_entries:
            card_data = get_card_data(card_name)
            sideboard_with_data.append((card_name, count, card_data))
            time.sleep(0.1)
        display_card_grid(sideboard_with_data, n_cols=5)
