#!/usr/bin/env python3
from PIL import Image
import sys
from typing import Union


class Print:
    colours = {"red": "\033[91m", "yellow": "\033[93m", "reset": "\033[0m"}

    @staticmethod
    def error(*message, sep=" "):
        sys.stderr.write(
            f"{Print.colours['red']}Error: {sep.join(map(str, message))}{Print.colours['reset']}\n"
        )
        sys.exit(1)

    @staticmethod
    def warn(*message, sep=" "):
        sys.stderr.write(
            f"{Print.colours['yellow']}Warning: {sep.join(map(str, message))}{Print.colours['reset']}\n"
        )

    @staticmethod
    def info(*message, sep=" "):
        sys.stdout.write(f"{sep.join(map(str, message))}\n")

    @staticmethod
    # does not print anything but colours the message
    def colour(message, colour):
        return f"{Print.colours[colour]}{message}{Print.colours['reset']}"


class ProcessImage:
    def __init__(self, image_path):
        self.image_path = image_path
        self._image = None
        self._spritemap = None
        self._used_colours = None
        self._size = None

    def _load_image(self):
        try:
            with Image.open(self.image_path) as img:
                if img.mode != "P":
                    Print.warn(f"Image {self.image_path} is not in index mode")
                return img.copy()
        except Exception as e:
            Print.error(f"failed to load image, {type(e).__name__}, {e}")

    def _load_spritemap(self):
        width, height = self.image.size
        pixels = list(self.image.getdata())
        return tuple(tuple(pixels[i * width : (i + 1) * width]) for i in range(height))

    @staticmethod
    def get_used_colours(spritemap: tuple) -> set:
        return set(pix for row in spritemap for pix in row)

    @property
    def image(self):
        if self._image is None:
            self._image = self._load_image()
        return self._image

    @property
    def spritemap(self):
        if self._spritemap is None:
            self._spritemap = self._load_spritemap()
        return self._spritemap

    @property
    def used_colours(self):
        if self._used_colours is None:
            self._used_colours = self.get_used_colours(self.spritemap)
        return self._used_colours

    @property
    def size(self):
        if self._size is None:
            self._size = self.image.size
        return self._size


class ProcessedImage:
    def __init__(self, spritemap):
        self.spritemap = spritemap
        self.image_path = "Internal image"
        self._used_colours = None
        self._size = None

    @property
    def used_colours(self) -> set:
        if self._used_colours is None:
            self._used_colours = ProcessImage.get_used_colours(self.spritemap)
        return self._used_colours

    @property
    def size(self):
        if self._size is None:
            self._size = (len(self.spritemap[0]), len(self.spritemap))
        return self._size


class CompareImage:
    def __init__(self, patient1, patient2):
        if not patient1.size == patient2.size:
            Print.info(patient1.size, patient2.size)
            Print.error(
                f"Images {patient1.image_path} and {patient2.image_path} are not the same size"
            )

        self.patient1 = patient1
        self.patient2 = patient2

        self._rec_info = None
        self._spritemap = None
        self._recolour_dict1 = None
        self._recolour_dict2 = None
        self._used_colours = None
        self._estimated_colour_count = None

    @property
    def rec_info(self):
        if self._rec_info is None:
            self._rec_info = self.get_recinfo(self.patient1, self.patient2)
        return self._rec_info

    @property
    def spritemap(self):
        if self._spritemap is None:
            self._spritemap, self._recolour_dict1, self._recolour_dict2 = self.rec_info
        return self._spritemap

    @property
    def recolour_dict1(self):
        if self._recolour_dict1 is None:
            self._spritemap, self._recolour_dict_1, self._recolour_dict2 = self.rec_info
        return self._recolour_dict1

    @property
    def recolour_dict2(self):
        if self._recolour_dict2 is None:
            self._spritemap, self._recolour_dict_1, self._recolour_dict2 = self.rec_info
        return self._recolour_dict2

    @property
    def used_colours(self):
        if self._used_colours is None:
            self._used_colours = len(ProcessImage.get_used_colours(self.spritemap))
        return self._used_colours

    @property
    def estimated_colour_count(self):
        if self._estimated_colour_count is None:
            colours1 = len(self.patient1.used_colours)
            colours2 = len(self.patient2.used_colours)
            self._estimated_colour_count = (
                max(colours1, colours2),
                colours1 * colours2,
            )
        return self._estimated_colour_count

    @staticmethod
    def get_recinfo(
        image1: Union[ProcessImage, ProcessedImage],
        image2: Union[ProcessImage, ProcessedImage],
    ) -> tuple[tuple, dict, dict]:
        # data initialization
        new_spritemap = [
            [0 for _ in range(len(image1.spritemap[0]))]
            for _ in range(len(image1.spritemap))
        ]
        recolour_dict1 = {_: _ for _ in range(256)}
        recolour_dict2 = {_: _ for _ in range(256)}
        processed_coords = set()

        common_colours = image1.used_colours & image2.used_colours

        for colour1 in image1.used_colours:
            coords1 = tuple(
                (x, y)
                for x, row in enumerate(image1.spritemap)
                for y, pix in enumerate(row)
                if pix == colour1
            )
            for coord in coords1:
                if coord in processed_coords:
                    continue
                colour2 = image2.spritemap[coord[0]][coord[1]]
                coords2 = tuple(
                    (x, y)
                    for x, row in enumerate(image2.spritemap)
                    for y, pix in enumerate(row)
                    if pix == colour2
                )
                final_coords = set(coords1) & set(coords2)
                processed_coords |= final_coords
                if colour1 == colour2:
                    for coord in final_coords:
                        new_spritemap[coord[0]][coord[1]] = colour1
                else:
                    new_colour = 0
                    while new_colour in common_colours:
                        new_colour += 1
                        if new_colour > 255:
                            Print.error(
                                "impossible to process as image requires more than 256 colours"
                            )
                    common_colours |= {new_colour}
                    for coord in final_coords:
                        new_spritemap[coord[0]][coord[1]] = new_colour
                    recolour_dict1[new_colour] = colour1
                    recolour_dict2[new_colour] = colour2

        return (tuple(new_spritemap), recolour_dict1, recolour_dict2)


def gen_recolour_sprite(rec1, rec2):
    rec_copy = rec1.copy()
    for dkey, dval in rec2.items():
        rec_copy[dkey] = rec1[dval]

    return rec_copy


def process_image(image_paths: list[str]) -> tuple:
    images = [ProcessImage(image_path) for image_path in image_paths]
    new_image = CompareImage(images[0], images[1])
    Print.info(
        f"Estimated colours: {new_image.estimated_colour_count[0]}-{new_image.estimated_colour_count[1]}"
    )
    Print.info(f"Actual           : {new_image.used_colours}")
    spritemap = new_image.spritemap
    rec1 = new_image.recolour_dict1
    rec2 = new_image.recolour_dict2

    recolour_sprites = {image_paths[0]: rec1.copy(), image_paths[1]: rec2.copy()}
    processed = ProcessedImage(spritemap)

    for i in range(2, len(images)):
        new_image = CompareImage(processed, images[i])
        Print.info(
            f"Estimated colours: {new_image.estimated_colour_count[0]}-{new_image.estimated_colour_count[1]}"
        )
        Print.info(f"Actual           : {new_image.used_colours}")
        processed.spritemap = new_image.spritemap

        for key, recolour_sprite in recolour_sprites.items():
            recolour_sprites[key] = gen_recolour_sprite(
                recolour_sprite, new_image.recolour_dict1
            )

        recolour_sprites[image_paths[i]] = new_image.recolour_dict2

    return (processed.spritemap, images[0].image.getpalette(), recolour_sprites)


def write_image(filename: str, data: tuple, palette: Image.Palette) -> None:
    new_image = Image.new("P", (len(data[0]), len(data)))
    new_image.putdata([item for sublist in data for item in sublist])
    new_image.putpalette(palette)
    new_image.save(filename)


def format_recolour_data(recolour_data: dict[dict]) -> dict:
    f = {}
    for name, rec in recolour_data.items():
        s = ""
        s += "recolour_sprite {"
        s += f"\n    // {name}"
        counter = 0
        for key, value in rec.items():
            if key == value:
                continue
            if counter % 8 == 0:
                s += "\n    "
            s += f"0x{key:02x}:0x{value:02x};"
            counter += 1
        s += "\n}\n"
        Print.info(f"Used colours: {counter} ({name})")
        f[name] = s
    return f


def write_recolour(filename: str, recolour_data: dict[dict]) -> None:
    with open(filename, "w+") as f:
        for rec in format_recolour_data(recolour_data).values():
            f.write(rec)
    Print.info(f"Recolour data written to {filename}")


def copyright():
    from datetime import datetime

    Print.info("blend.py - A tool to blend multiple images together")
    Print.info(f"Copyright 2024-{datetime.now().year} WenSim <wensimehrp@gmail.com>")
    Print.info("Licensed under the MIT License")
    Print.info("")


def main():
    import time

    start = time.time()

    copyright()

    if len(sys.argv) < 2:
        Print.error(
            "Please provide at least one image to process\nUsage: blend.py <image1> <image2> ..."
        )
        sys.exit(1)

    if sys.argv[1] in ("-h", "--help", "-?"):
        Print.info("Usage: blend.py <image1> <image2> ...")
        sys.exit(0)

    if len(sys.argv) > 3:
        Print.warn(
            "You are processing more than 3 images, this may use a lot of colours"
        )

    files = sys.argv[1:]

    spritemap, palette, recs = process_image(files)
    write_image("output.png", spritemap, palette)
    write_recolour("recolour.txt", recs)

    Print.info("Finished processing images")
    Print.info(f"Time taken: {time.time() - start:.2f}s")


if __name__ == "__main__":
    main()
