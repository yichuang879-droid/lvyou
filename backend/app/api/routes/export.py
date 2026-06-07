"""导出路由 —— Markdown / PDF 行程单导出。"""
from urllib.parse import quote
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, Response
from app.services.export_service import itinerary_to_markdown, itinerary_to_pdf_bytes
from app.services.storage_service import get_itinerary_by_trip_id, save_itinerary

router = APIRouter(prefix="/export", tags=["export"])


def _build_filename_header(filename: str) -> dict[str, str]:
    return {"Content-Disposition": f"inline; filename*=UTF-8''{quote(filename)}"}


@router.get("/{trip_id}/markdown", response_class=PlainTextResponse)
def export_trip_markdown(trip_id: str) -> PlainTextResponse:
    """把已保存 itinerary 导出为 Markdown 文本。"""
    detail = get_itinerary_by_trip_id(trip_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Trip not found.")
    markdown = itinerary_to_markdown(detail)
    return PlainTextResponse(content=markdown, media_type="text/markdown; charset=utf-8",
                             headers=_build_filename_header(f"{trip_id}.md"))


@router.get("/{trip_id}/pdf", response_class=Response)
def export_trip_pdf(trip_id: str) -> Response:
    """把已保存 itinerary 导出为 PDF。"""
    detail = get_itinerary_by_trip_id(trip_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Trip not found.")
    try:
        pdf_bytes = itinerary_to_pdf_bytes(detail)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers=_build_filename_header(f"{trip_id}.pdf"))
