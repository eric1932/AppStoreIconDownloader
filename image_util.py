import base64


def show_image_in_terminal(image_name, image_binary, image_length: int):
    b64_name = base64.b64encode(image_name.encode('utf-8')).decode('utf-8')  # in case of non-ascii chars
    b64_img = base64.b64encode(image_binary).decode('ascii')  # decode to remove the b'___' wrapping
    print(f"\n"
          f"\033]1337;File="
          f"name={b64_name}"
          f"size={len(image_binary)};"
          f"width={image_length}px;"
          f"height={image_length}px;"
          f"inline=1:{b64_img}\a")
