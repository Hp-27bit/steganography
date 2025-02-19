import cv2
import os

# Load the image
img = cv2.imread("mypic.jpg")  # Replace with the correct image path

# Input secret message and passcode
msg = input("Enter secret message: ")
password = input("Enter a passcode: ")

# Create ASCII dictionaries
d = {chr(i): i for i in range(255)}

# Embed the message into the image
n, m, z = 0, 0, 0
for i in range(len(msg)):
    img[n, m, z] = d[msg[i]]
    n += 1
    m += 1
    z = (z + 1) % 3

# Save the encrypted image
cv2.imwrite("encryptedImage.jpg", img)
os.system("start encryptedImage.jpg")  # Opens the image on Windows

# Save the password to a separate file (for decryption purposes)
with open("password.txt", "w") as file:
    file.write(password)

print("Message encrypted and saved as 'encryptedImage.jpg'.")
