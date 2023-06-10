import re
import math
import logging

MESSAGE_LENGTH_CONTAINER_RGB = 1
MESSAGE_LENGTH_CONTAINER_GRAYSCALE = 3


def _get_binary_seq(s):
    return bin(int(s.encode().hex(), base=16))[2:]


def str_to_bin(s):
    if not s:
        return ''
    zfill = 8 - len(_get_binary_seq(s[0]))
    return '0' * zfill + _get_binary_seq(s)


def split_byte_seq(s, each=8):
    return re.findall('.' * each, s)


def binary_to_string(bits):
    return ''.join([chr(int(i, base=2)) for i in bits])


def calc_capacity(pixels, data_bits=1):
    data_bits = 8 // (data_bits if data_bits < 3 else 1)
    return pixels // data_bits


def generate_primes():
    """ Generate an infinite sequence of prime numbers."""
    D = {}

    q = 2

    while True:
        if q not in D:
            yield q
            D[q * q] = [q]
        else:
            for p in D[q]:
                D.setdefault(p + q, []).append(p)
            del D[q]

        q += 1


def find_largest_prime(n):
    prime_generator = generate_primes()
    t = next(prime_generator)
    p = None

    while t < n:
        p = t
        t = next(prime_generator)

    return p


def prime_factorization(p):
    factors = []
    prime_div = 2

    while prime_div * prime_div <= p:
        if p % prime_div == 0:
            factors.append(prime_div)
            p //= prime_div
        else:
            prime_div += 1

    if p > 1:
        factors.append(p)

    return factors


def euler_phi(n):
    prime_factors_set = set(prime_factorization(n))
    phi = n
    for i in prime_factors_set:
        phi *= (1 - 1 / i)
    return int(phi)


def find_all_divisors(x, exclude_one=False):
    return [i for i in range(1 if not exclude_one else 2, x + 1) if x % i == 0]


def mod_p(x, p):
    return x % p


def find_primitive_element(p):
    possible_orders = find_all_divisors(p - 1, exclude_one=True)
    a = 2
    is_primitive = False

    while a < p - 1 and not is_primitive:
        i = 0
        while pow(a, possible_orders[i], p) != 1 and i < len(possible_orders):
            i += 1

        is_primitive = i == len(possible_orders) - 1

        if not is_primitive:
            a += 1

    if is_primitive:
        return a

    return None


def find_primitive_roots(p):
    powers = [i for i in range(1, p) if math.gcd(i, p - 1) == 1]
    primitive_element = find_primitive_element(p)
    return [pow(primitive_element, power, p) for power in powers]


def find_primitive_root_largest(p):
    return max(find_primitive_roots(p))


def inject_into_pixel_rgb(pixel, bits):
    new_pixel = tuple()
    for p, b in zip(pixel, bits):
        new_pixel += (inject_into_pixel_value(p, b),)
    if len(new_pixel) != 3:
        new_pixel += pixel[len(new_pixel):]
    return new_pixel


def inject_into_pixel_value(value, bit):
    return int(bin(value)[2:-len(bit)] + bit, base=2)


def extract_from_pixel_rgb(pixel, bits=1):
    seq = ''
    for p in pixel:
        seq += extract_from_pixel_value(p, bits)
    return seq


def extract_from_pixel_value(value, bits=1):
    return bin(value & int(('1' * bits).rjust(8, '0'), base=2))[2:].zfill(bits)


def pixel_index_to_loc(pixel_index, img_width):
    # convert to xy coordinates within image
    loc_x = pixel_index % img_width
    loc_y = pixel_index // img_width
    return loc_x, loc_y


def default_mode(image):
    """ convert to default color space """
    mode = 'L'
    # RGB
    if image.mode in ["CMYK", "HSV", "RGB", "RGBA", "RGBX", "YCbCr"]:
        mode = 'RGB'

    # grayscale
    if image.mode in ["L", "LA"]:
        mode = 'L'

    if image.mode != mode:
        image = image.convert(mode)

    return image, mode


def hide_message(image, message: str):
    im_width, im_height = image.size
    total_pixels = im_width * im_height
    logging.info(f"Total pixels in the image: {total_pixels}")

    # convert to default color space
    image, mode = default_mode(image)
    logging.info(f"Image mode: {mode}")

    # pixels containing hidden message length
    message_length_pixels = MESSAGE_LENGTH_CONTAINER_RGB if mode == 'RGB' else MESSAGE_LENGTH_CONTAINER_GRAYSCALE

    # find the largest prime and largest primitive root
    capacity_pixels = total_pixels - message_length_pixels
    largest_prime = find_largest_prime(capacity_pixels)
    logging.info(f"Largest prime that satisfy P<L: {largest_prime}<{capacity_pixels}")

    largest_prime = find_largest_prime(total_pixels - message_length_pixels)
    largest_primitive_root = find_primitive_root_largest(largest_prime)  # y = A^i mod p  => A
    logging.info(f"Largest primitive root: {largest_primitive_root}")

    bin_str = str_to_bin(message)
    capacity = calc_capacity(total_pixels - message_length_pixels)
    logging.info(f"Image capacity: {capacity}")
    if capacity < len(bin_str):
        raise Exception('no enough capacity')

    # calculate number of pixels needed to hide the message
    cipher_pixels = len(message) * 8
    if mode == 'RGB':
        cipher_pixels = math.ceil(cipher_pixels / 3)

    # split bits sequence into list containing single bit elements
    bit_seq = split_byte_seq(bin_str, each=1)

    # start modifying pixels
    for i in range(1, cipher_pixels + 1):
        # find pixel index to hide message bit
        cipher_pixel_index = pow(largest_primitive_root, i, largest_prime)
        loc = pixel_index_to_loc(cipher_pixel_index, im_width)

        pixel = image.getpixel(loc)
        if mode == 'RGB':
            new_pixel = inject_into_pixel_rgb(pixel, bit_seq[(i - 1) * 3:(i - 1) * 3 + 3])
        else:
            new_pixel = inject_into_pixel_value(pixel, bit_seq[i - 1])
        image.putpixel(loc, new_pixel)

    # save message length into last pixels
    cipher_pixels_count = len(bin_str)
    if mode == 'RGB':
        cipher_pixels_count = math.ceil(cipher_pixels_count / 3)

    message_length_binary = bin(cipher_pixels_count)[2:].rjust(24, '0')
    message_length_int = [int(x, base=2) for x in split_byte_seq(message_length_binary)]

    if mode == 'RGB':
        loc = pixel_index_to_loc(total_pixels - 1, im_width)
        image.putpixel(loc, tuple(message_length_int))
    else:
        for i in range(message_length_pixels - 1, -1, -1):
            loc = pixel_index_to_loc(total_pixels - 1 - i, im_width)
            image.putpixel(loc, message_length_int[3 - i - 1])

    # save modified image
    image.save("STEGO_IMG.png", "PNG")


def reveal_message(image):
    im_width, im_height = image.size
    total_pixels = im_width * im_height
    logging.info(f"Total pixels in the image: {total_pixels}")

    # convert to default color space
    image, mode = default_mode(image)
    logging.info(f"Image mode: {mode}")

    # pixels containing hidden message length
    message_length_pixels = MESSAGE_LENGTH_CONTAINER_RGB if mode == 'RGB' else MESSAGE_LENGTH_CONTAINER_GRAYSCALE

    # get message length from last pixels
    message_length_int = []
    if mode == 'RGB':
        loc = pixel_index_to_loc(total_pixels - 1, im_width)
        pixel_value = image.getpixel(loc)
        message_length_int = list(pixel_value)
        logging.info(f"MESSAGE LENGTH FROM LAST PIXELS -> PIXEL VALUE: {pixel_value}")
    else:
        for i in range(message_length_pixels - 1, -1, -1):
            loc = pixel_index_to_loc(total_pixels - 1 - i, im_width)
            pixel_value = image.getpixel(loc)
            message_length_int.append(pixel_value)
            logging.info(f"MESSAGE LENGTH FROM LAST PIXELS -> PIXEL VALUE: {pixel_value}")

    # convert to binary vector
    message_length_binary = ''.join([bin(x)[2:].rjust(8, '0') for x in message_length_int])
    logging.info(f"MESSAGE LENGTH FROM LAST PIXELS BINARY: {message_length_binary}")
    message_length = int(message_length_binary, base=2)
    logging.info(f"MESSAGE LENGTH FROM LAST PIXELS: {message_length}")

    # find the largest prime and largest primitive root
    capacity_pixels = total_pixels - message_length_pixels
    largest_prime = find_largest_prime(capacity_pixels)
    logging.info(f"Largest prime that satisfy M<P<L: {message_length}<{largest_prime}<{capacity_pixels}")
    largest_primitive_root = find_primitive_root_largest(largest_prime)
    logging.info(f"Largest primitive root: {largest_primitive_root}")

    capacity = calc_capacity(total_pixels - message_length_pixels)
    logging.info(f"Image capacity: {capacity}")
    if capacity < message_length:
        raise Exception('No message hidden message as capacity does not match message length obtained from last pixels')

    # reveal message
    bins = []
    for i in range(1, message_length + 1):
        cipher_pixel_index = pow(largest_primitive_root, i, largest_prime)
        loc = pixel_index_to_loc(cipher_pixel_index, im_width)
        pixel = image.getpixel(loc)
        if mode == 'RGB':
            bins.append(extract_from_pixel_rgb(pixel))
        else:
            bins.append(extract_from_pixel_value(pixel))

    new_bin_seq = ''.join(bins)
    new_byte_seq = split_byte_seq(new_bin_seq)
    return binary_to_string(new_byte_seq)
