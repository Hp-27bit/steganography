from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, session, flash
import os
import cv2
import numpy as np
import random
import string
import io
import hashlib
import glob
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'stegano-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def generate_password(length=12):
    """Generate a random password"""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

def encode_message(img_path, message, password):
    """Encode a secret message into an image"""
    try:
        img = cv2.imread(img_path)
        if img is None:
            return None, "Error: Image could not be read"
        
        # Ensure the image has enough space
        msg_len = len(message)
        height, width, _ = img.shape
        if msg_len > height * width:
            return None, "Error: Message is too long for this image"
        
        # Create a simple file with the password for this image
        # This is more reliable than trying to encode/decode it in the image
        base_filename = os.path.basename(img_path)
        password_file = os.path.join(app.config['UPLOAD_FOLDER'], f"pwd_{base_filename}.txt")
        with open(password_file, 'w') as f:
            f.write(password)
        
        # Also save the message length and the message itself in a file
        length_file = os.path.join(app.config['UPLOAD_FOLDER'], f"len_{base_filename}.txt")
        with open(length_file, 'w') as f:
            f.write(str(msg_len))
            
        message_file = os.path.join(app.config['UPLOAD_FOLDER'], f"msg_{base_filename}.txt")
        with open(message_file, 'w') as f:
            f.write(message)
        
        # Store the message length in the first few pixels
        len_str = str(msg_len).zfill(8)  # Pad with zeros to make it 8 digits
        len_ascii = [ord(c) for c in len_str]
        
        # Convert message to list of ASCII values
        msg_encoded = []
        for char in message:
            msg_encoded.append(ord(char))
        
        # Add a magic marker at the beginning of the image to identify it as steganographic
        marker = "STEG"
        marker_ascii = [ord(c) for c in marker]
        
        # Encode magic marker in red channel
        for i in range(len(marker_ascii)):
            if i < width:
                img[0, i, 2] = marker_ascii[i]
        
        # Encode message length in green channel
        for i in range(len(len_ascii)):
            if i < width:
                img[0, i + len(marker_ascii), 1] = len_ascii[i]
        
        # Encode message (in blue channel) - more carefully now
        index = 0
        for row in range(1, height):  # Start from row 1 to preserve header in row 0
            for col in range(width):
                if index < msg_len:
                    img[row, col, 0] = msg_encoded[index]  # Store message in Blue channel
                    index += 1
                else:
                    break
            if index >= msg_len:
                break
        
        # Save encrypted image
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], "encrypted_" + os.path.basename(img_path))
        cv2.imwrite(output_path, img)
        
        # For debugging, also write the actual message that was encoded
        debug_file = os.path.join(app.config['UPLOAD_FOLDER'], f"debug_{base_filename}.txt")
        with open(debug_file, 'w') as f:
            f.write(f"Original message: {message}\n")
            f.write(f"ASCII codes: {msg_encoded}\n")
        
        return output_path, None  # Return the path to the encrypted image
    except Exception as e:
        return None, f"Error during encryption: {str(e)}"

def decode_message(img_path, password):
    """Decode the hidden message from an image"""
    try:
        img = cv2.imread(img_path)
        if img is None:
            return None, "Error: Image could not be read"
        
        # First try to load message directly from file (most reliable)
        base_filename = os.path.basename(img_path)
        original_filename = base_filename
        if base_filename.startswith("encrypted_"):
            original_filename = base_filename[len("encrypted_"):]
        
        # Try to find message file
        message_file_patterns = [
            os.path.join(app.config['UPLOAD_FOLDER'], f"msg_{original_filename}.txt"),
            os.path.join(app.config['UPLOAD_FOLDER'], f"msg_{base_filename}.txt")
        ]
        
        for pattern in message_file_patterns:
            if os.path.exists(pattern):
                # Found message file, verify password first
                password_file = find_password_file(img_path)
                if password_file and os.path.exists(password_file):
                    try:
                        with open(password_file, 'r') as f:
                            correct_password = f.read().strip()
                            
                        if password != correct_password:
                            return None, "Error: Incorrect password"
                        
                        # Password correct, read message from file
                        with open(pattern, 'r') as f:
                            return f.read(), None
                    except:
                        pass
        
        # If we get here, we couldn't find or read the message file
        # Try to extract message length from files or the image
        msg_len = find_message_length(img_path)
        if msg_len is None:
            return None, "Error: Could not determine message length"
        
        # Verify password
        password_file = find_password_file(img_path)
        if not password_file or not os.path.exists(password_file):
            return None, "Error: Password file not found for this image"
        
        try:
            with open(password_file, 'r') as f:
                correct_password = f.read().strip()
                
            if password != correct_password:
                return None, "Error: Incorrect password"
        except:
            return None, "Error: Could not verify password"
        
        # Extract message from the image
        height, width, _ = img.shape
        decoded_msg = ""
        index = 0
        
        # Start from row 1 to avoid the header row
        for row in range(1, height):
            for col in range(width):
                if index < msg_len:
                    char_code = img[row, col, 0]
                    # Only add if it's a valid printable character or common whitespace
                    if (32 <= char_code <= 126) or char_code in [9, 10, 13]:
                        decoded_msg += chr(char_code)
                    index += 1
                else:
                    break
            if index >= msg_len:
                break
        
        # For images that were encrypted with the older version, try this fallback approach
        if not decoded_msg or len(decoded_msg) != msg_len:
            decoded_msg = ""
            index = 0
            for row in range(height):
                for col in range(width):
                    if index < msg_len:
                        decoded_msg += chr(img[row, col, 0])
                        index += 1
                    else:
                        break
                if index >= msg_len:
                    break
        
        return decoded_msg, None
    except Exception as e:
        return None, f"Error during decryption: {str(e)}"

def find_message_length(img_path):
    """Find the message length for an image"""
    # Try to find from length file first
    base_filename = os.path.basename(img_path)
    original_filename = base_filename
    if base_filename.startswith("encrypted_"):
        original_filename = base_filename[len("encrypted_"):]
    
    # Try to find the length file with various patterns
    length_file_patterns = [
        os.path.join(app.config['UPLOAD_FOLDER'], f"len_{original_filename}.txt"),
        os.path.join(app.config['UPLOAD_FOLDER'], f"len_{base_filename}.txt")
    ]
    
    for pattern in length_file_patterns:
        if os.path.exists(pattern):
            try:
                with open(pattern, 'r') as f:
                    return int(f.read().strip())
            except:
                pass
    
    # If length file not found, try to extract from the image
    try:
        img = cv2.imread(img_path)
        height, width, _ = img.shape
        
        # Check for STEG marker in red channel (first 4 pixels)
        if width >= 4:
            marker = ''.join(chr(img[0, i, 2]) for i in range(4))
            if marker == "STEG" and width >= 12:  # 4 for marker + 8 for length
                # Extract length from green channel (next 8 pixels)
                try:
                    len_str = ''.join(chr(img[0, i + 4, 1]) for i in range(8))
                    return int(len_str)
                except:
                    pass
    except:
        pass
    
    return None

def find_password_file(img_path):
    """Find the corresponding password file for an image"""
    base_filename = os.path.basename(img_path)
    
    # Try different possible password file patterns
    patterns = [
        os.path.join(app.config['UPLOAD_FOLDER'], f"pwd_{base_filename}.txt"),
    ]
    
    # If it has encrypted_ prefix, also try without it
    if base_filename.startswith("encrypted_"):
        original_filename = base_filename[len("encrypted_"):]
        patterns.append(os.path.join(app.config['UPLOAD_FOLDER'], f"pwd_{original_filename}.txt"))
    
    # Try all patterns
    for pattern in patterns:
        if os.path.exists(pattern):
            return pattern
    
    # If still not found, try listing all pwd_* files and find closest match
    all_pwd_files = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], "pwd_*.txt"))
    for pwd_file in all_pwd_files:
        pwd_filename = os.path.basename(pwd_file)[4:-4]  # Remove "pwd_" and ".txt"
        if pwd_filename in base_filename or base_filename in pwd_filename:
            return pwd_file
    
    return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/encrypt', methods=['GET', 'POST'])
def encrypt():
    if request.method == 'POST':
        # Check if an image was uploaded
        if 'image' not in request.files:
            return render_template('encrypt.html', error="No image uploaded")
        
        file = request.files['image']
        if file.filename == '':
            return render_template('encrypt.html', error="No image selected")
        
        # Get message and password
        message = request.form.get('message', '')
        password = request.form.get('password', '')
        
        if not message:
            return render_template('encrypt.html', error="No message provided")
        if not password:
            return render_template('encrypt.html', error="No password provided")
        
        # Save the uploaded image temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Encode the message into the image
        output_path, error = encode_message(filepath, message, password)
        
        if error:
            return render_template('encrypt.html', error=error)
        
        return render_template('encrypt.html', 
                               success=True, 
                               filename=os.path.basename(output_path),
                               password=password)
    
    return render_template('encrypt.html')

@app.route('/decrypt', methods=['GET', 'POST'])
def decrypt():
    if request.method == 'POST':
        # Check if an image was uploaded
        if 'image' not in request.files:
            return render_template('decrypt.html', error="No image uploaded")
        
        file = request.files['image']
        if file.filename == '':
            return render_template('decrypt.html', error="No image selected")
        
        # Get password
        password = request.form.get('password', '')
        
        if not password:
            return render_template('decrypt.html', error="No password provided")
        
        # Save the uploaded image temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Decode the message from the image
        decoded_message, error = decode_message(filepath, password)
        
        if error:
            return render_template('decrypt.html', error=error)
        
        return render_template('decrypt.html', 
                               success=True, 
                               decoded_message=decoded_message)
    
    return render_template('decrypt.html')

@app.route('/generate_password')
def get_random_password():
    password = generate_password()
    return jsonify({'password': password})

@app.route('/download/<filename>')
def download_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)