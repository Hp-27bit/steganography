import cv2

# Load the encrypted image
img = cv2.imread("encryptedImage.jpg")  # Ensure the image is in the same folder

# Load the saved password from the encryption phase
with open("password.txt", "r") as file:
    saved_password = file.read()

# Create reverse ASCII dictionary
c = {i: chr(i) for i in range(255)}

# Input passcode for decryption
entered_password = input("Enter passcode for Decryption: ")

# Decryption process
if entered_password == saved_password:
    message = ""
    n, m, z = 0, 0, 0
    for i in range(img.shape[0] * img.shape[1]):  # Go through all pixels
        char_value = img[n, m, z]
        if char_value == 0:  # Stop if we reach unmodified pixels (optional)
            break
        message += c[char_value]
        n += 1
        m += 1
        z = (z + 1) % 3
    print("Decryption message:", message)
else:
    print("YOU ARE NOT AUTHORIZED")
