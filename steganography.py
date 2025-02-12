import cv2
import os
import numpy as np

# Load the image
img = cv2.imread("mypic.jpg")  # Replace with your image file
if img is None:
    print("Error: Image not found!")
    exit()

msg = input("Enter secret message: ")
password = input("Enter a passcode: ")

# Ensure the image has enough space
msg_len = len(msg)
height, width, _ = img.shape
if msg_len > height * width:
    print("Error: Message is too long for this image.")
    exit()

# Convert message to list of ASCII values
msg_encoded = [ord(c) for c in msg]

# Encode message into the image
index = 0
for row in range(height):
    for col in range(width):
        if index < msg_len:
            img[row, col, 0] = msg_encoded[index]  # Store in Blue channel
            index += 1
        else:
            break
    if index >= msg_len:
        break

# Save encrypted image
cv2.imwrite("encryptedImage.jpg", img)
os.system("start encryptedImage.jpg")  # Open the image on Windows

# Decryption
pas = input("Enter passcode for Decryption: ")
if password == pas:
    decoded_msg = ""
    index = 0
    for row in range(height):
        for col in range(width):
            if index < msg_len:
                decoded_msg += chr(img[row, col, 0])  # Retrieve from Blue channel
                index += 1
            else:
                break
        if index >= msg_len:
            break
    print("Decryption message:", decoded_msg)
else:
    print("YOU ARE NOT AUTHORIZED")
