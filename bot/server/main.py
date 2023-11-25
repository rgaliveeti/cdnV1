from quart import Blueprint, Response, request
from .error import abort
from bot import TelegramBot
from math import ceil, floor
from bot.modules.telegram import get_message, get_file_properties

bp = Blueprint('main', __name__)


@bp.route('/')
async def home():
    return Response({"status": "running"})


@bp.route('/<int:channel_id>/<int:file_id>/<string:fileName>')
async def transmit_file(channel_id, file_id, fileName):
    file = await get_message(channel_id=int(channel_id), message_id=int(file_id)) or abort(404)
    range_header = request.headers.get('Range', 0)

    file_name, file_size, mime_type = get_file_properties(file)

    if range_header:
        from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
        from_bytes = int(from_bytes)
        until_bytes = int(until_bytes) if until_bytes else file_size - 1
    else:
        from_bytes = 0
        until_bytes = file_size - 1

    if (until_bytes > file_size) or (from_bytes < 0) or (until_bytes < from_bytes):
        abort(416, 'Invalid range.')

    chunk_size = 1024 * 1024
    until_bytes = min(until_bytes, file_size - 1)

    offset = from_bytes - (from_bytes % chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = until_bytes % chunk_size + 1

    req_length = until_bytes - from_bytes + 1
    part_count = ceil(until_bytes / chunk_size) - floor(offset / chunk_size)

    headers = {
        "Content-Type": f"{mime_type}",
        "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
        "Content-Length": str(req_length),
        "Content-Disposition": f'attachment; filename="{fileName}"',
        "Accept-Ranges": "bytes",
    }

    async def file_generator():
        current_part = 1
        async for chunk in TelegramBot.iter_download(file, offset=offset, chunk_size=chunk_size, stride=chunk_size,
                                                     file_size=file_size):
            if not chunk:
                break
            elif part_count == 1:
                yield chunk[first_part_cut:last_part_cut]
            elif current_part == 1:
                yield chunk[first_part_cut:]
            elif current_part == part_count:
                yield chunk[:last_part_cut]
            else:
                yield chunk

            current_part += 1

            if current_part > part_count:
                break

    return Response(file_generator(), headers=headers, status=206 if range_header else 200)
