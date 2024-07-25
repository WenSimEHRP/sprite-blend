#!/usr/bin/env python3
from PIL import Image
import sys
from typing import *

class Print:
    colours = {
        "red": "\033[91m",
        "yellow": "\033[93m",
        "reset": "\033[0m"
    }

    @staticmethod
    def error(message):
        sys.stderr.write(f"{Print.colours["red"]}Error: {message}{Print.colours["reset"]}\n")

    @staticmethod
    def warn(message):
        sys.stderr.write(f"{Print.colours["yellow"]}Warning: {message}{Print.colours["reset"]}\n")

    @staticmethod
    def info(message):
        sys.stdout.write(f"{message}\n")


class ProcessImage:
    def __init__(self, image_path):
        self.image_path: str    = image_path
        self.image: Image.Image = self.load_image
        self.tuple: tuple       = self.to_2d_tuple if isinstance(self.image, Image.Image) else None
        if not self.check_index_mode: Print.error(f"Image {image_path} is not in index mode.")
        self.used_colours: set  = self.get_used_colours

    @property
    def load_image(self) -> Image.Image | bool:
        try:
            with Image.open(self.image_path) as img:
                return img.copy()
        except Exception as e:
            Print.error(f"{type(e)}, {e}")
            sys.exit(1)

    @property
    def check_index_mode(self) -> bool:
        return False if not isinstance(self.image, Image.Image) else self.image.mode == "P"

    @property
    def to_2d_tuple(self) -> tuple:
        width, height = self.image.size
        pixels = list(self.image.getdata())
        return tuple(
            tuple(pixels[i * width:(i + 1) * width])
                  for i in range(height))

    @property
    def get_used_colours(self) -> set:
        return set(self.image.getdata())

class CompareImage:
    def __init__(self, patient1, patient2):
        self.patient1 = patient1
        self.patient2 = patient2
        self._compare_state = None
        self._tuple = None
        self._recolour_dict1 = None
        self._recolour_dict2 = None
        if not self.same_size:
            Print.error("Images are not the same size")
            sys.exit(1)

    @property
    def check_instance(self) -> bool:
        return isinstance(self.patient1, ProcessImage) and isinstance(self.patient2, ProcessImage)

    @staticmethod
    def same_size(compare1: ProcessImage, compare2: ProcessImage) -> bool:
        return compare1.image.size == compare2.image.size

    @property
    def compare_state(self) -> bool:
        if self._compare_state is None:
            self._compare_state = self.compare(self.patient1, self.patient2)
        return self._compare_state

    @property
    def my_tuple(self) -> tuple:
        if self._tuple is None or self._recolour_dict1 is None or self._recolour_dict2 is None:
            self._tuple, self._recolour_dict1, self._recolour_dict2 = self.new_tuple(self.patient1, self.patient2)
        return self._tuple, self._recolour_dict1, self._recolour_dict2

    @staticmethod
    def compare(compare1: ProcessImage, compare2: ProcessImage) -> bool:
        return compare1.tuple == compare2.tuple

    @staticmethod
    def new_tuple(compare1, compare2) -> tuple:
        new_list = [[0 for _ in range(len(compare1.tuple[0]))] for _ in range(len(compare1.tuple))]
        # dict initialization
        recolour_dict1 = {x:x for x in range(256)}
        recolour_dict2 = {x:x for x in range(256)}
        processed_coords = set()

        common_colours = compare1.used_colours & compare2.used_colours

        for colour in compare1.used_colours:
            coords1 = [(x, y) for y, row in enumerate(compare1.tuple) for x, pix in enumerate(row) if pix == colour]
            for coord in coords1:
                if coord in processed_coords: continue
                colour2 = compare2.tuple[coord[1]][coord[0]]
                coords2 = [(x, y) for y, row in enumerate(compare2.tuple) for x, pix in enumerate(row) if pix == colour2]
                final_coords:set = set(coords1) & set(coords2)
                processed_coords |= final_coords
                if colour == colour2:
                    for coord in final_coords:
                        new_list[coord[1]][coord[0]] = colour
                else:
                    new_colour = 0
                    while new_colour in common_colours:
                        new_colour += 1
                        if new_colour > 255:
                            Print.error("new colour exceeded 255, exiting")
                            sys.exit(1)
                    common_colours |= {new_colour}
                    for coord in final_coords:
                        new_list[coord[1]][coord[0]] = new_colour
                    recolour_dict1[new_colour] = colour
                    recolour_dict2[new_colour] = colour2

        Print.info(f"Current number of colours: {len(common_colours)}")
        return (tuple(new_list), recolour_dict1, recolour_dict2, common_colours)

def write_image(filename: str, data: tuple, palette: Image.Palette) -> None:
    new_image = Image.new("P", (len(data[0]), len(data)))
    new_image.putdata([item for sublist in data for item in sublist])
    new_image.putpalette(palette)
    new_image.save(filename)

def process_image(image_paths: list[str]) -> tuple:
    class ProcessedImage:
        tuple = None
        used_colours = None

    images = [ProcessImage(image_path) for image_path in image_paths]
    spritemap, rec1, rec2, colours = CompareImage.new_tuple(images[0], images[1])

    recolour_sprites = [rec1.copy(), rec2.copy()]
    processed        = ProcessedImage()
    processed.tuple  = spritemap
    processed.used_colours = colours

    for i in range(2, len(images)):
        spritemap, base_rec, new_rec, colours = CompareImage.new_tuple(processed, images[i])
        processed.tuple = spritemap
        processed.used_colours |= colours

        for i, recolour_sprite in enumerate(recolour_sprites):
            my_copy = recolour_sprite.copy()
            for dkey, dval in base_rec.items():
                recolour_sprite[dkey] = my_copy[dval]

            recolour_sprites[i] = recolour_sprite

        recolour_sprites.append(new_rec)

    return (processed.tuple, images[0].image.getpalette(), recolour_sprites)


def main():
    import time
    start = time.time()

    files = sys.argv[1:] if len(sys.argv) > 1 else [".\\platform_cement_asym_1.png", ".\\wood.png", ".\\real_asym_1.png"]

    # if len(sys.argv) < 3:
    #     Print.error("Paths not specified\nUsage: blend.py <image1> <image2>")
    #     sys.exit(1)

    # file1 = ProcessImage(sys.argv[1])
    # file2 = ProcessImage(sys.argv[2])
    # Print.info(f"Processing {sys.argv[1]} and {sys.argv[2]}")
    # spritemap, rec1, rec2 = CompareImage(file1, file2).my_tuple
    spritemap, palette, recs = process_image(files)
    write_image("output.png", spritemap, palette)

    with open("recolour.txt", "w+") as f:
        for ind, rec in enumerate(recs):
            f.write("recolour_sprite {")
            f.write(f"\n    // {files[ind]}")
            counter = 0
            for key, value in rec.items():
                if key == value: continue
                if counter % 8 == 0:
                    f.write("\n   ")
                f.write(f" {key:<3}: {value:<3};")
                counter += 1
            f.write("\n}\n")
        Print.info("Recolour data written to recolour.txt")

    Print.info("Finished processing images")
    Print.info(f"Time taken: {time.time() - start:.2f}s")

if __name__ == "__main__":
    main()
