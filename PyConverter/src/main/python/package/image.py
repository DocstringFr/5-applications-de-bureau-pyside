import os

from PIL import Image


class CustomImage:
    def __init__(self, path, folder="reduced"):
        self.image = Image.open(path)
        self.width, self.height = self.image.size
        self.path = path
        self.reduced_path = os.path.join(os.path.dirname(self.path),
                                         folder,
                                         os.path.basename(self.path))

    def reduce_image(self, size=0.5, quality=75):
        new_width = round(self.width * size)
        new_height = round(self.height * size)
        self.image = self.image.resize((new_width, new_height), Image.ANTIALIAS)
        parent_dir = os.path.dirname(self.reduced_path)

        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        self.image.save(self.reduced_path, 'JPEG', quality=quality)
        return os.path.exists(self.reduced_path)


if __name__ == '__main__':
    i = CustomImage("/Users/thibh/Pictures/_sample_images/20180210-IMG_3121.jpg")
    i.reduce_image(size=1, quality=50)