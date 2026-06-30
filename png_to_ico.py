from PIL import Image
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
img = Image.open("icon.png")
img.save("icon.ico", format="ICO", sizes=[(16,16), (32,32), (48,48), (256,256)])