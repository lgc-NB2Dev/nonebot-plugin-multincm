from dataclasses import dataclass
from io import BytesIO
from math import ceil
from pathlib import Path
from typing import List, Optional, Sequence, Union

from pil_utils import BuildImage, Text2Image
from pil_utils.types import ColorType, HAlignType

from .config import config
from .types import SongSearchResult

BACKGROUND = BuildImage.open(Path(__file__).parent / "res" / "bg.jpg")


@dataclass()
class TableHead:
    name: str
    align: HAlignType = "left"
    min_width: Optional[int] = None
    max_width: Optional[int] = None


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


def draw_table(
    heads: Sequence[Union[TableHead, str]],
    lines: Sequence[Sequence[str]],
    fontsize: int = 30,
    pic_padding: int = 2,
    item_padding_w: int = 10,
    item_padding_h: int = 15,
    border_width: int = 3,
    border_radius: int = 15,
    font_color: ColorType = (255, 255, 255, 255),
    border_color: ColorType = (255, 255, 255, 120),
    **kwargs,
) -> BuildImage:
    head_len = len(heads)
    for li in lines:
        if len(li) != head_len:
            raise ValueError("line length not match head length")

    line_len = len(lines)
    heads = [TableHead(x) if isinstance(x, str) else x for x in heads]

    line_texts: List[List[Text2Image]] = [
        [
            generate_line_text(
                head,
                f"[b]{head.name}[/b]",
                fontsize=fontsize,
                fill=font_color,
                **kwargs,
            )
            for head in heads
        ],
    ]
    for line in lines:
        line_texts.append(
            [
                generate_line_text(
                    heads[i],
                    x,
                    fontsize=fontsize,
                    fill=font_color,
                    **kwargs,
                )
                for i, x in enumerate(line)
            ],
        )

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


def format_alias(name: str, alias: List[str]) -> str:
    return f'{name}（{"；".join(alias)}）' if alias else name


def format_time(time: int) -> str:
    s, _ = divmod(time, 1000)
    m, s = divmod(s, 60)
    return f"{m:0>2d}:{s:0>2d}"


def draw_search_res(res: SongSearchResult, page_num: int = 1) -> BytesIO:
    pic_padding = 50
    table_padding = 20
    table_border_radius = 15

    table = draw_table(
        [
            TableHead("序号", align="right"),
            TableHead("歌名", max_width=600),
            TableHead("歌手", max_width=400),
            TableHead("时长", align="center"),
            TableHead("热度", align="center"),
        ],
        [
            [
                f"[b]{i+1}[/b]",
                format_alias(x.name, x.alia),
                "、".join([format_alias(y.name, y.alias) for y in x.ar]),
                format_time(x.dt),
                f"{int(x.pop)}",
            ]
            for i, x in enumerate(res.songs)
        ],
        border_radius=table_border_radius,
    )

    max_page = ceil(res.songCount / config.ncm_list_limit)
    title_txt = Text2Image.from_text(
        "歌曲列表",
        80,
        weight="bold",
        fill=(255, 255, 255),
        fontname=config.ncm_list_font or "",
    )
    footer_txt = Text2Image.from_bbcode_text(
        (
            f"第 [b]{page_num}[/b] / [b]{max_page}[/b] 页 | 共 [b]{res.songCount}[/b] 首\n"
            "Tip：发送序号选择；发送 [b]上一页[/b] 或 [b]下一页[/b] 来翻页；发送 [b]退出[/b] 退出选择"
        ),
        30,
        align="center",
        fill=(255, 255, 255),
        fontname=config.ncm_list_font or "",
    )

    width = table.width + pic_padding * 2 + table_padding * 2
    height = table.height + title_txt.height + footer_txt.height + table_padding * 6

    bg = BACKGROUND.copy().convert("RGBA").resize((width, height), keep_ratio=True)
    title_txt.draw_on_image(bg.image, ((width - title_txt.width) // 2, table_padding))
    bg.paste(
        (
            BuildImage.new(
                "RGBA",
                (table.width + table_padding * 2, table.height + table_padding * 2),
                (0, 0, 0, 80),
            ).circle_corner(table_border_radius)
        ),
        (pic_padding, title_txt.height + table_padding * 2),
        alpha=True,
    )
    bg.paste(
        table,
        (
            pic_padding + table_padding,
            title_txt.height + table_padding * 3,
        ),
        alpha=True,
    )
    footer_txt.draw_on_image(
        bg.image,
        ((width - footer_txt.width) // 2, height - table_padding - footer_txt.height),
    )

    return bg.save_jpg()