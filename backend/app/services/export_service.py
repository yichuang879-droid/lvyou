"""导出服务 —— Markdown + PDF 格式的行程单导出。"""
from __future__ import annotations
from io import BytesIO
from xml.sax.saxutils import escape
from app.models.schemas import TripDetailResponse, Itinerary

TECHNICAL_EXPORT_KEYWORDS = (
    "LLM", "RAG", "LangChain", "Chroma", "演示", "测试",
    "规则", "模型", "源码", "trip_service",
)


def _safe_text(value: object) -> str:
    return escape(str(value or ""))


def _clean_export_tips(tips: list[str]) -> list[str]:
    return list(dict.fromkeys([
        t.strip() for t in tips
        if t.strip() and not any(k in t for k in TECHNICAL_EXPORT_KEYWORDS)
    ]))


def itinerary_to_markdown(trip_detail: TripDetailResponse) -> str:
    """把完整 itinerary 渲染成 Markdown。"""
    it = trip_detail.itinerary
    lines = [
        f"# {it.destination} 行程单",
        "",
        f"- 行程 ID：{trip_detail.trip_id}",
        f"- 目的地：{it.destination}",
        f"- 预计预算：{it.estimated_budget:.2f} 元",
        "",
        "## 行程概述",
        it.summary,
        "",
        "## 每日安排",
    ]
    for day in it.days:
        theme = f" {day.theme}" if day.theme else ""
        lines.extend([
            "",
            f"### Day {day.day_index}{theme}",
            f"- 日期：{day.date.isoformat()}" if day.date else "- 日期：待定",
        ])
        for spot in day.spots:
            lines.extend([
                f"- 主要景点：{spot.name}",
                f"  - 时间：{spot.start_time or '待定'} - {spot.end_time or '待定'}",
                f"  - 说明：{spot.description or '无'}",
            ])
        for meal in day.meals:
            lines.extend([
                f"- 餐饮建议：{meal.name}（{meal.meal_type}）",
                f"  - 说明：{meal.notes or '无'}",
            ])
        if day.hotel:
            lines.append(f"- 住宿安排：{day.hotel.name}（{day.hotel.level or '未标注档次'}）")
        for note in day.notes:
            lines.append(f"- 备注：{note}")

    budget = it.budget_breakdown
    lines.extend([
        "", "## 预算拆分",
        f"- 交通：{budget.transport:.2f} 元",
        f"- 住宿：{budget.hotel:.2f} 元",
        f"- 餐饮：{budget.meals:.2f} 元",
        f"- 门票：{budget.tickets:.2f} 元",
        f"- 其他：{budget.other:.2f} 元",
        f"- 总计：{budget.total:.2f} 元",
    ])
    export_tips = _clean_export_tips(it.tips)
    if export_tips:
        lines.extend(["", "## 旅行提示"] + [f"- {t}" for t in export_tips])
    return "\n".join(lines).strip() + "\n"


def itinerary_to_pdf_bytes(trip_detail: TripDetailResponse) -> bytes:
    """把完整 itinerary 渲染成 PDF 二进制。"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
        )
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    except ImportError as exc:
        raise RuntimeError("PDF 导出依赖 reportlab，请先安装：pip install reportlab") from exc

    font_name = "STSong-Light"
    try:
        pdfmetrics.getFont(font_name)
    except KeyError:
        pdfmetrics.registerFont(UnicodeCIDFont(font_name))

    it = trip_detail.itinerary
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=16*mm, rightMargin=16*mm, topMargin=14*mm, bottomMargin=14*mm,
        title=f"{trip_detail.trip_id}.pdf",
    )
    base = getSampleStyleSheet()
    t_style = ParagraphStyle("T", parent=base["Title"], fontName=font_name, fontSize=22, leading=28, textColor=colors.HexColor("#16324f"), wordWrap="CJK")
    s_style = ParagraphStyle("S", parent=base["Heading2"], fontName=font_name, fontSize=13.5, leading=19, textColor=colors.HexColor("#0f4c5c"), spaceBefore=10, spaceAfter=6, wordWrap="CJK")
    b_style = ParagraphStyle("B", parent=base["BodyText"], fontName=font_name, fontSize=10.5, leading=15, textColor=colors.HexColor("#222"), wordWrap="CJK")

    story = [
        Paragraph(f"{_safe_text(it.destination)} 行程单", t_style),
        Paragraph(f"行程 ID：{_safe_text(trip_detail.trip_id)}<br/>预计预算：{it.estimated_budget:.2f} 元", b_style),
        Paragraph("行程概述", s_style),
        Paragraph(_safe_text(it.summary), b_style),
    ]
    story.append(Paragraph("每日安排", s_style))
    for day in it.days:
        title = f"Day {day.day_index}"
        if day.theme:
            title += f" · {day.theme}"
        story.append(Paragraph(title, ParagraphStyle("D", parent=s_style, fontSize=12, leading=17, spaceBefore=6, spaceAfter=4)))
        for spot in day.spots:
            story.append(Paragraph(f"景点：{_safe_text(spot.name)}", b_style))
            story.append(Paragraph(f"时间：{_safe_text(spot.start_time or '待定')} - {_safe_text(spot.end_time or '待定')}", b_style))
        for meal in day.meals:
            story.append(Paragraph(f"餐饮：{_safe_text(meal.name)}（{_safe_text(meal.meal_type)}）", b_style))
        if day.hotel:
            story.append(Paragraph(f"住宿：{_safe_text(day.hotel.name)}（{_safe_text(day.hotel.level or '未标注')}）", b_style))

    budget = it.budget_breakdown
    budget_table = Table([
        ["项目", "金额（元）"],
        ["交通", f"{budget.transport:.2f}"],
        ["住宿", f"{budget.hotel:.2f}"],
        ["餐饮", f"{budget.meals:.2f}"],
        ["门票", f"{budget.tickets:.2f}"],
        ["其他", f"{budget.other:.2f}"],
        ["总计", f"{budget.total:.2f}"],
    ], colWidths=[48*mm, 48*mm])
    budget_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9edf7")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd2d9")),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([Paragraph("预算拆分", s_style), budget_table])

    export_tips = _clean_export_tips(it.tips)
    if export_tips:
        story.append(Paragraph("旅行提示", s_style))
        for tip in export_tips:
            story.append(Paragraph(f"- {_safe_text(tip)}", b_style))

    doc.build(story)
    return buffer.getvalue()
