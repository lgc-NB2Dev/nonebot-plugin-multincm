from dataclasses import dataclass
from typing import List, Literal, Optional, Sequence

from pil_utils import BuildImage, Text2Image
from pil_utils.types import ColorType

AlignType = Literal["left", "middle", "right"]


@dataclass()
class TableHead:
    name: str
    align: AlignType = "left"
    min_width: Optional[int] = None
    max_width: Optional[int] = None


def generate_line_text(head: TableHead, text: str, **kwargs) -> Text2Image:
    text2img = Text2Image.from_bbcode_text(text, **kwargs)

    width = text2img.width
    max_width = head.max_width
    if max_width is not None and width > max_width:
        text2img.wrap(max_width)

    return text2img


def calculate_width(head: TableHead, now_max_width: int) -> int:
    # max_width = head.max_width
    min_width = head.min_width

    if min_width is not None and now_max_width < min_width:
        return min_width
    # if max_width is not None and now_max_width > max_width:
    #     return max_width

    return now_max_width


def calculate_pos_offset(align: AlignType, max_len: int, item_len: int) -> int:
    if align == "middle":
        return (max_len - item_len) // 2
    if align == "right":
        return max_len - item_len
    # default left
    return 0


def draw_table(
    heads: Sequence[TableHead],
    lines: Sequence[Sequence[str]],
    fontsize: int = 30,
    pic_padding: int = 2,
    item_padding: int = 8,
    border_width: int = 3,
    border_radius: int = 10,
    font_color: ColorType = (0, 0, 0, 255),
    border_color: ColorType = (0, 0, 0, 255),
) -> BuildImage:
    head_len = len(heads)
    line_len = len(lines)
    for li in lines:
        if len(li) != head_len:
            raise ValueError("line length not match head length")

    line_texts: List[List[Text2Image]] = [
        [
            generate_line_text(
                head,
                f"[b]{head.name}[/b]",
                fontsize=fontsize,
                fill=font_color,
            )
            for head in heads
        ],
    ]
    for line in lines:
        line_texts.append(
            [
                generate_line_text(heads[i], x, fontsize=fontsize, fill=font_color)
                for i, x in enumerate(line)
            ],
        )

    col_widths = [
        calculate_width(x, max([y[i].width for y in line_texts]))
        for i, x in enumerate(heads)
    ]

    total_pic_padding = pic_padding * 2
    total_item_padding = item_padding * head_len * 2

    total_item_width = sum(col_widths)
    total_border_width = border_width * (head_len + 1)

    total_item_height = sum([max([y.height for y in x]) for x in line_texts])
    total_border_height = border_width * (len(line_texts) + 1)

    width = (
        total_pic_padding + total_item_width + total_border_width + total_item_padding
    )
    height = total_pic_padding + total_item_height + total_border_height

    pic = BuildImage.new("RGBA", (width, height), (0, 0, 0, 0))

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

    y_offset = pic_padding + border_width
    for line_index, line in enumerate(line_texts):
        x_offset = pic_padding + item_padding + border_width
        line_height = max([x.height for x in line])

        for col_index, (head, item_width, item) in enumerate(
            zip(heads, col_widths, line),
        ):
            item.draw_on_image(
                pic.image,
                (
                    x_offset + calculate_pos_offset(head.align, item_width, item.width),
                    y_offset + calculate_pos_offset("middle", line_height, item.height),
                ),
            )

            # 写第一行字时画表格竖线，忽略第一列左侧
            if line_index == 0 and col_index != 0:
                border_x = x_offset - item_padding - border_width // 2
                pic.draw_line(
                    (border_x, pic_padding, border_x, height - pic_padding),
                    fill=border_color,
                    width=border_width,
                )

            x_offset += item_width + item_padding * 2 + border_width

        y_offset += line_height + border_width

        # 画表格横线，忽略最后一行下方
        if line_index != line_len:
            border_y = y_offset - border_width // 2
            pic.draw_line(
                (pic_padding, border_y, width - pic_padding, border_y),
                fill=border_color,
                width=border_width,
            )

    return pic


if __name__ == "__main__":
    table = draw_table(
        [
            TableHead("姓名", "left"),
            TableHead("国籍", "middle"),
            TableHead("职业", "middle"),
            TableHead("简介", "left", max_width=500),
        ],
        [
            ["张三", "中国", "医生", "张三是一名资深的医生，擅长各种疾病的治疗。"],
            ["John Smith", "美国", "演员", "John Smith是一名出色的演员，曾经获得过多项奥斯卡奖。"],
            ["Marie Dupont", "法国", "作家", "Marie Dupont是一位著名的法国作家，她的作品畅销全球。"],
            ["Hiroshi Tanaka", "日本", "工程师", "Hiroshi Tanaka是一位优秀的工程师，他曾主导多个重要项目的开发。"],
        ],
    )
    bg = (
        BuildImage.new("RGBA", table.size, (255, 255, 255))
        .paste(table, alpha=True)
        .image.show()
    )
