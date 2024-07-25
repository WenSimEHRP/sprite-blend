#!/usr/bin/env python3
from PIL import Image
import sys

class Print:
    colours = {
        'red': '\033[91m',
        'yellow': '\033[93m',
        'reset': '\033[0m'
    }

    @staticmethod
    def error(message):
        sys.stderr.write(f"{Print.colours['red']}Error: {message}{Print.colours['reset']}\n")

    @staticmethod
    def warn(message):
        sys.stderr.write(f"{Print.colours['yellow']}Warning: {message}{Print.colours['reset']}\n")

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
        return False if not isinstance(self.image, Image.Image) else self.image.mode == 'P'

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
    def __init__(self, image1, image2):
        self.patient1: ProcessImage = image1
        self.patient2: ProcessImage = image2
        if not self.check_instance:
            raise ValueError("Both images must be of type ProcessImage.")
        if not self.same_size(self.patient1, self.patient2):
            Print.error("Both images must be the same size.")
        self._compare_state  = None
        self._tuple          = None

    @property
    def check_instance(self):
        return isinstance(self.patient1, ProcessImage) and isinstance(self.patient2, ProcessImage)

    @staticmethod
    def same_size(compare1: ProcessImage, compare2: ProcessImage) -> bool:
        return compare1.image.size == compare2.image.size

    @property
    def compare_state(self):
        if self._compare_state is None:
            self._compare_state = self.compare(self.patient1, self.patient2)
        return self._compare_state

    @property
    def my_tuple(self):
        if self._tuple is None or self._recolour_dict1 is None or self._recolour_dict2 is None:
            self._tuple, self._recolour_dict1, self._recolour_dict2 = self.new_tuple(self.patient1, self.patient2)
        return self._tuple, self._recolour_dict1, self._recolour_dict2

    @staticmethod
    def compare(compare1: ProcessImage, compare2: ProcessImage) -> bool:
        return False if compare1.tuple != compare2.tuple else True

    @staticmethod
    def new_tuple(compare1: ProcessImage, compare2: ProcessImage) -> tuple[tuple, dict, dict]:

        new_list = [[0 for _ in range(len(compare1.tuple[0]))] for _ in range(len(compare1.tuple))]
        recolour_dict1 = {}
        recolour_dict2 = {}
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
                            Print.error("No more colours available. Try reducing the number of colours in the palette.")
                            sys.exit(1)
                    common_colours |= {new_colour}
                    for coord in final_coords:
                        new_list[coord[1]][coord[0]] = new_colour
                    recolour_dict1[new_colour] = colour
                    recolour_dict2[new_colour] = colour2


        return (tuple(new_list), recolour_dict1, recolour_dict2)


def write_image(filename: str, data: tuple, palette: Image.Palette) -> None:
    new_image = Image.new("P", (len(data[0]), len(data)))
    new_image.putdata([item for sublist in data for item in sublist])
    new_image.putpalette(palette)
    new_image.save(filename)

def main():
    import time
    start = time.time()

    if len(sys.argv) < 3:
        Print.error("Paths not specified\nUsage: blend.py <image1> <image2>")
        sys.exit(1)

    file1 = ProcessImage(sys.argv[1])
    file2 = ProcessImage(sys.argv[2])
    Print.info(f"Processing {sys.argv[1]} and {sys.argv[2]}")
    spritemap, rec1, rec2 = CompareImage(file1, file2).my_tuple
    write_image("output.png", spritemap, file1.image.getpalette())

    with open("recolour.txt", "w+") as f:
        for rec in (rec1, rec2):
            f.write("recolour_sprite {")
            counter = 0
            for key, value in rec.items():
                if counter % 4 == 0:
                    f.write("\n    ")
                # fix trailing spaces
                if (counter+1) % 4 == 0 or counter == len(rec) - 1:
                    f.write(f"{key:<3}: {value:<3};")
                # normal output
                else:
                    f.write(f"{key:<3}: {value:<3};  ")
                counter += 1
            f.write("\n}\n")
        Print.info("Recolour data written to recolour.txt")

    Print.info("Finished processing images")
    Print.info(f"Time taken: {time.time() - start:.2f}s")

if __name__ == "__main__":
    main()
