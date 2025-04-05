# app.py
import streamlit as st
import os, zipfile, shutil
import json
from collections import Counter, defaultdict
import heapq

# --- Huffman Compression Logic ---
class Node:
    def __init__(self, char=None, freq=0):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(text):
    freq_map = Counter(text)
    heap = [Node(char, freq) for char, freq in freq_map.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        node1 = heapq.heappop(heap)
        node2 = heapq.heappop(heap)
        merged = Node(freq=node1.freq + node2.freq)
        merged.left = node1
        merged.right = node2
        heapq.heappush(heap, merged)

    return heap[0] if heap else None

def build_codes(node, current_code="", codes={}):
    if node is None:
        return
    if node.char is not None:
        codes[node.char] = current_code
    build_codes(node.left, current_code + "0", codes)
    build_codes(node.right, current_code + "1", codes)
    return codes

def compress_file(input_path, output_path, codes_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    root = build_huffman_tree(text)
    codes = build_codes(root)
    encoded_text = ''.join(codes[char] for char in text)

    padded_encoded = encoded_text + '0' * ((8 - len(encoded_text) % 8) % 8)
    byte_array = bytearray()
    for i in range(0, len(padded_encoded), 8):
        byte = padded_encoded[i:i+8]
        byte_array.append(int(byte, 2))

    with open(output_path, 'wb') as f:
        f.write(bytes(byte_array))

    with open(codes_path, 'w') as f:
        json.dump(codes, f)

# --- Huffman Decompression Logic ---
def decompress_file(input_bin_path, codes_json_path, output_path):
    with open(input_bin_path, 'rb') as f:
        byte_data = f.read()
        bit_string = ''.join(f"{byte:08b}" for byte in byte_data)

    with open(codes_json_path, 'r') as f:
        codes = json.load(f)
    reverse_codes = {v: k for k, v in codes.items()}

    current = ""
    decoded_text = []
    for bit in bit_string:
        current += bit
        if current in reverse_codes:
            decoded_text.append(reverse_codes[current])
            current = ""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(decoded_text))

# --- Streamlit App ---
st.set_page_config(page_title="Huffman Encoder/Decoder", layout="centered")
st.title("🧠 Huffman Compression Web App")

tab1, tab2 = st.tabs(["📦 Compress", "🧩 Decompress"])

# 📦 Compression Tab
with tab1:
    st.subheader("Upload a Text File to Compress")
    file = st.file_uploader("Upload .txt file", type=['txt'])

    if file:
        input_path = f"temp/{file.name}"
        compressed_path = "output/compressed.bin"
        codes_path = "output/codes.json"
        zip_path = "output/huffman_package.zip"

        os.makedirs("temp", exist_ok=True)
        os.makedirs("output", exist_ok=True)

        with open(input_path, "wb") as f:
            f.write(file.read())

        compress_file(input_path, compressed_path, codes_path)

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(compressed_path, arcname="compressed.bin")
            zipf.write(codes_path, arcname="codes.json")

        st.success("File compressed successfully!")
        with open(zip_path, "rb") as f:
            st.download_button("📁 Download ZIP Package", f, file_name="huffman_package.zip")

# 🧩 Decompression Tab
with tab2:
    st.subheader("Upload Huffman Package to Decompress")
    zip_file = st.file_uploader("Upload ZIP", type=['zip'])

    if zip_file:
        zip_path = "temp/huffman_input.zip"
        extract_dir = "temp/decode"
        os.makedirs(extract_dir, exist_ok=True)

        with open(zip_path, "wb") as f:
            f.write(zip_file.read())

        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(extract_dir)

        try:
            decompress_file(
                input_bin_path=os.path.join(extract_dir, "compressed.bin"),
                codes_json_path=os.path.join(extract_dir, "codes.json"),
                output_path="output/decoded.txt"
            )
            with open("output/decoded.txt", "rb") as f:
                st.download_button("📄 Download Decoded File", f, file_name="decoded.txt")
                st.success("Decoded successfully!")
        except Exception as e:
            st.error(f"Error: {e}")
