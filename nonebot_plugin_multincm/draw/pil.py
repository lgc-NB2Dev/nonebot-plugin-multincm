from typing import List, Sequence, Union

from pil_utils import BuildImage, Text2Image
from pil_utils.types import ColorType, HAlignType

from ..config import config
from ..const import RES_DIR
from .shared import TableHead, TablePage

BACKGROUND = BuildImage.open(RES_DIR / "bg.jpg")


def calculate_width(head: TableHead, now_max_width: int) -> int:
    # max_width = head.max_width
    min_width = head.min_width

    if min_width is not None and now_max_width < min_width:
        return min_width
    # if max_width is not None and now_max_width > max_width:
    #     return max_width

    return now_max_width


def calculate_pos_offset(align: HAlignType, max_len: int, item_len: int) -> int:
    if align == "center":
        return (max_len - item_len) // 2
    if align == "right":
        return max_len - item_len
    # default left
    return 0


def generate_line_text(head: TableHead, text: str, **kwargs) -> Text2Image:
    text2img = Text2Image.from_bbcode_text(
        text,
        align=head.align,
        fontname=config.ncm_list_font or "",
        **kwargs,
    )

    width = text2img.width
    max_width = head.max_width
    if max_width is not None and width > max_width:
        text2img.wrap(max_width)

    return text2img


def draw_table(
    heads: Sequence[Union[TableHead, str]],
    lines: Sequence[Sequence[str]],
    border_radius: int = 15,
    **kwargs,
) -> BuildImage:
    font_size = 30
    pic_padding = 2
    item_padding_w = 10
    item_padding_h = 15
    border_width = 3
    font_color = (255, 255, 255, 255)
    border_color = (255, 255, 255, 100)

    head_len = len(heads)
    for li in lines:
        if len(li) != head_len:
            raise ValueError("line length not match head length")

    line_len = len(lines)
    heads = [TableHead(x) if isinstance(x, str) else x for x in heads]

    head_line_text = [
        generate_line_text(
            head,
            f"[b]{head.name}[/b]",
            fontsize=font_size,
            fill=font_color,
            **kwargs,
        )
        for head in heads
    ]
    body_line_texts = [
        [
            generate_line_text(
                heads[i],
                x,
                fontsize=font_size,
                fill=font_color,
                **kwargs,
            )
            for i, x in enumerate(line)
        ]
        for line in lines
    ]
    line_texts: List[List[Text2Image]] = [head_line_text, *body_line_texts]

    col_widths = [
        calculate_width(x, max([y[i].width for y in line_texts]))
        for i, x in enumerate(heads)
    ]

    total_pic_padding = pic_padding * 2
    total_item_padding_w = item_padding_w * head_len * 2
    total_item_padding_h = item_padding_h * (line_len + 1) * 2

    total_item_width = sum(col_widths)
    total_border_width = border_width * (head_len + 1)

    total_item_height = sum([max([y.height for y in x]) for x in line_texts])
    total_border_height = border_width * (len(line_texts) + 1)

    width = (
        total_pic_padding + total_item_width + total_border_width + total_item_padding_w
    )
    height = (
        total_pic_padding
        + total_item_height
        + total_border_height
        + total_item_padding_h
    )

    pic = BuildImage.new("RGBA", (width, height), (255, 255, 255, 0))

    # 画表格框
    pic.draw_rounded_rectangle(
        (
            pic_padding,
            pic_padding,
            width - pic_padding,
            height - pic_padding,
        ),
        border_radius,
        outline=border_color,
        width=border_width,
    )

    y_offset = pic_padding + item_padding_h + border_width
    for line_index, line in enumerate(line_texts):
        x_offset = pic_padding + item_padding_w + border_width
        line_height = max([x.height for x in line])

        for col_index, (head, item_width, item) in enumerate(
            zip(heads, col_widths, line),
        ):
            item.draw_on_image(
                pic.image,
                (
                    x_offset + calculate_pos_offset(head.align, item_width, item.width),
                    y_offset + calculate_pos_offset("center", line_height, item.height),
                ),
            )

            # 写第一行字时画表格竖线，忽略第一列左侧
            if line_index == 0 and col_index != 0:
                border_x = x_offset - item_padding_w - border_width // 2
                pic.draw_line(
                    (border_x, pic_padding, border_x, height - pic_padding),
                    fill=border_color,
                    width=border_width,
                )

            x_offset += item_width + item_padding_w * 2 + border_width

        y_offset += line_height + item_padding_h * 2 + border_width

        # 画表格横线，忽略最后一行下方
        if line_index != line_len:
            border_y = y_offset - item_padding_h - border_width // 2
            pic.draw_line(
                (pic_padding, border_y, width - pic_padding, border_y),
                fill=border_color,
                width=border_width,
            )

    return pic


async def draw_table_page(res: TablePage) -> bytes:
    pic_padding = 50
    table_padding = 20
    table_border_radius = 15

    heads, lines = res.table
    table_img = draw_table(heads, lines, border_radius=table_border_radius)

    calling = res.calling
    title_txt = Text2Image.from_text(
        f"{calling}列表",
        80,
        weight="bold",
        fill=(255, 255, 255),
        fontname=config.ncm_list_font or "",
    )
    tip_txt = Text2Image.from_bbcode_text(
        (
            f"Tip：[b]发送序号[/b] 选择{calling} | 发送 [b]P[/b]+[b]数字[/b] 跳到指定页数\n"
            "其他操作：[b]上一页[/b](P) | [b]下一页[/b](N) | [b]退出[/b](E)"
        ),
        30,
        align="center",
        fill=(255, 255, 255),
        fontname=config.ncm_list_font or "",
    )
    footer_txt = Text2Image.from_bbcode_text(
        f"第 [b]{res.current_page}[/b] / [b]{res.max_page}[/b] 页 | 共 [b]{res.max_count}[/b] 首",
        30,
        align="center",
        fill=(255, 255, 255),
        fontname=config.ncm_list_font or "",
    )

    width = table_img.width + pic_padding * 2 + table_padding * 2
    height = (
        table_img.height
        + title_txt.height
        + tip_txt.height
        + footer_txt.height
        + table_padding * 7
    )

    bg = BACKGROUND.copy().convert("RGBA").resize((width, height), keep_ratio=True)
    y_offset = table_padding

    title_txt.draw_on_image(bg.image, ((width - title_txt.width) // 2, y_offset))
    y_offset += title_txt.height + table_padding

    tip_txt.draw_on_image(bg.image, ((width - tip_txt.width) // 2, y_offset))
    y_offset += tip_txt.height + table_padding

    bg.paste(
        (
            BuildImage.new(
                "RGBA",
                (
                    table_img.width + table_padding * 2,
                    table_img.height + table_padding * 2,
                ),
                (255, 255, 255, 50),
            ).circle_corner(table_border_radius)
        ),
        (pic_padding, y_offset),
        alpha=True,
    )
    y_offset += table_padding

    bg.paste(table_img, (pic_padding + table_padding, y_offset), alpha=True)
    y_offset += table_img.height + table_padding * 2

    footer_txt.draw_on_image(bg.image, ((width - footer_txt.width) // 2, y_offset))

    return bg.save_jpg((0, 0, 0)).getvalue()


async def str_to_pic(
    txt: str,
    padding: int = 20,
    font_color: ColorType = (241, 246, 249),
    bg_color: ColorType = (33, 42, 62),
    font_size: int = 30,
    text_align: HAlignType = "left",
) -> bytes:
    txt2img = Text2Image.from_bbcode_text(
        txt,
        fontname=config.ncm_list_font or "",
        fill=font_color,
        fontsize=font_size,
        align=text_align,
    )
    img = BuildImage.new(
        "RGBA",
        (txt2img.width + padding * 2, txt2img.height + padding * 2),
        bg_color,
    )
    txt2img.draw_on_image(img.image, (padding, padding))
    return img.save_jpg().getvalue()
