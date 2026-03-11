import cv2
import wave
import hashlib
import base64
import numpy as np
from PIL import Image
from cryptography.fernet import Fernet

END_MARK = "1111111111111110"

# ---------------- Encryption ----------------

def generate_key(password):
    key = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(key)

def encrypt(msg,password):
    f = Fernet(generate_key(password))
    return f.encrypt(msg.encode())

def decrypt(data,password):
    f = Fernet(generate_key(password))
    return f.decrypt(data).decode()

# ---------------- Utilities ----------------

def bytes_to_bin(data):
    return ''.join(format(b,'08b') for b in data)

def bin_to_bytes(binary):
    byte_array = [binary[i:i+8] for i in range(0,len(binary),8)]
    return bytes([int(b,2) for b in byte_array])

# ---------------- IMAGE STEGO ----------------

def encode_image(image_path,data,output):

    img = Image.open(image_path)
    pixels = img.load()

    binary = bytes_to_bin(data) + END_MARK
    index = 0

    for y in range(img.height):
        for x in range(img.width):

            r,g,b = pixels[x,y]

            if index < len(binary):
                r = (r & ~1) | int(binary[index]); index+=1
            if index < len(binary):
                g = (g & ~1) | int(binary[index]); index+=1
            if index < len(binary):
                b = (b & ~1) | int(binary[index]); index+=1

            pixels[x,y]=(r,g,b)

            if index>=len(binary):
                img.save(output)
                return

def decode_image(image_path):

    img = Image.open(image_path)
    pixels = img.load()

    binary=""

    for y in range(img.height):
        for x in range(img.width):

            r,g,b = pixels[x,y]

            binary+=str(r&1)
            binary+=str(g&1)
            binary+=str(b&1)

    binary=binary.split(END_MARK)[0]

    return bin_to_bytes(binary)

# ---------------- AUDIO STEGO ----------------

def encode_audio(audio_path,data,output):

    song = wave.open(audio_path,'rb')

    frame_bytes = bytearray(list(song.readframes(song.getnframes())))

    binary = bytes_to_bin(data)+END_MARK

    for i in range(len(binary)):
        frame_bytes[i] = (frame_bytes[i] & 254) | int(binary[i])

    new_audio = wave.open(output,'wb')
    new_audio.setparams(song.getparams())
    new_audio.writeframes(bytes(frame_bytes))

def decode_audio(audio_path):

    song = wave.open(audio_path,'rb')

    frame_bytes = bytearray(list(song.readframes(song.getnframes())))

    bits = [frame_bytes[i]&1 for i in range(len(frame_bytes))]

    chars=[]

    for i in range(0,len(bits),8):
        byte = bits[i:i+8]
        chars.append(chr(int("".join(map(str,byte)),2)))

    decoded="".join(chars)

    decoded=decoded.split("\xff\xfe")[0]

    return decoded.encode()

# ---------------- VIDEO STEGO ----------------

def encode_video(video_path,data,output):

    cap = cv2.VideoCapture(video_path)

    fourcc = cv2.VideoWriter_fourcc(*'XVID')

    out = cv2.VideoWriter(output,fourcc,20.0,
        (int(cap.get(3)),int(cap.get(4))))

    binary = bytes_to_bin(data)+END_MARK
    index=0

    while cap.isOpened():

        ret,frame = cap.read()
        if not ret: break

        for row in frame:
            for pixel in row:
                for i in range(3):
                    if index<len(binary):
                        pixel[i]=(pixel[i]&~1)|int(binary[index])
                        index+=1

        out.write(frame)

    cap.release()
    out.release()

# ---------------- MAIN MENU ----------------

print("""
===== Advanced Steganography Suite =====

1 Hide message in Image
2 Extract message from Image
3 Hide message in Audio
4 Extract message from Audio
5 Hide message in Video

""")

choice=input("Select option: ")

password=input("Password: ")

if choice=="1":

    img=input("Image file: ")
    msg=input("Secret message: ")
    out=input("Output image: ")

    enc=encrypt(msg,password)

    encode_image(img,enc,out)

    print("Message hidden in image.")

elif choice=="2":

    img=input("Encoded image: ")

    data=decode_image(img)

    print("Hidden message:",decrypt(data,password))

elif choice=="3":

    audio=input("Audio file: ")
    msg=input("Secret message: ")
    out=input("Output audio: ")

    enc=encrypt(msg,password)

    encode_audio(audio,enc,out)

elif choice=="4":

    audio=input("Encoded audio: ")

    data=decode_audio(audio)

    print("Hidden message:",decrypt(data,password))

elif choice=="5":

    video=input("Video file: ")
    msg=input("Secret message: ")
    out=input("Output video: ")

    enc=encrypt(msg,password)

    encode_video(video,enc,out)

    print("Message hidden in video.")
    input ("\nTask completed!press Enter to exit...")