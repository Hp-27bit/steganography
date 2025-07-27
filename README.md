# Steganography Web App

A web application for hiding and revealing secret messages in images using steganography techniques.

## Features

- **Encrypt**: Hide secret messages in images
  - Upload any image
  - Enter your secret message
  - Set a custom password or generate a random one
  - Download the encrypted image

- **Decrypt**: Reveal hidden messages from images
  - Upload an encrypted image
  - Enter the password
  - Enter the message length
  - View the decrypted message

## Installation and Setup

1. Clone this repository or download the source code

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - MacOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Run the application:
   ```
   python app.py
   ```

6. Open your web browser and navigate to `http://127.0.0.1:5000`

## How It Works

This application uses steganography techniques to hide messages within image files. The process modifies pixel values in the blue channel without significantly altering the image's appearance.

- **Encryption**: The secret message is converted to ASCII values, which are then embedded in the blue channel of the image pixels.
- **Decryption**: The ASCII values are extracted from the blue channel and converted back to characters to reveal the original message.

## Important Notes

- The message length must be saved during encryption for successful decryption
- The quality of steganography depends on the image size (larger images can hide longer messages)
- The encrypted image appears visually identical to the original image 