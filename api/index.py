import os
import re
from urllib.parse import urlparse

import yt_dlp
from flask import Flask, jsonify, request

app = Flask(__name__)


def is_instagram_url(url: str) -> bool:
    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        hostname = (parsed.hostname or "").lower()
        hostname = re.sub(r"^www\.", "", hostname)

        return (
            hostname == "instagram.com"
            or hostname.endswith(".instagram.com")
        )

    except Exception:
        return False


def clean_filename(filename: str) -> str:
    filename = re.sub(
        r'[\\/:*?"<>|]+',
        "_",
        filename
    )

    filename = filename.strip()

    if not filename:
        filename = "PaceFetch-download"

    return filename[:150]


@app.route("/api/download", methods=["GET"])
def download():

    instagram_url = request.args.get(
        "url",
        ""
    ).strip()

    if not instagram_url:
        return jsonify({
            "success": False,
            "error": "Instagram URL is required."
        }), 400

    if not is_instagram_url(instagram_url):
        return jsonify({
            "success": False,
            "error": "Only Instagram URLs are supported."
        }), 400

    try:

        options = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
            "extract_flat": False,

            "format": "best[ext=mp4]/best",

            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Linux; Android 10) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/120.0 "
                    "Mobile Safari/537.36"
                ),

                "Accept-Language":
                    "en-US,en;q=0.9"
            }
        }

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                instagram_url,
                download=False
            )

        if not info:
            return jsonify({
                "success": False,
                "error":
                    "Instagram did not return any media."
            }), 404

        media_url = info.get("url") or ""

        if not media_url:

            formats = info.get(
                "formats",
                []
            )

            available_formats = [
                item
                for item in formats
                if item.get("url")
            ]

            if available_formats:

                available_formats.sort(
                    key=lambda item:
                        item.get(
                            "height",
                            0
                        ) or 0,
                    reverse=True
                )

                media_url = (
                    available_formats[0]
                    .get("url", "")
                )

        if not media_url:
            return jsonify({
                "success": False,
                "error":
                    "No downloadable media URL was found."
            }), 404

        title = (
            info.get("title")
            or info.get("description")
            or "Instagram media"
        )

        title = str(title).strip()

        ext = (
            info.get("ext")
            or "mp4"
        )

        if ext.lower() == "unknown":
            ext = "mp4"

        filename = clean_filename(title)
        filename += "." + ext

        thumbnail = (
            info.get("thumbnail")
            or ""
        )

        duration = info.get("duration")

        return jsonify({
            "success": True,
            "title": title,
            "media_url": media_url,
            "thumbnail": thumbnail,
            "duration": duration,
            "filename": filename,
            "type": "video"
        })

    except yt_dlp.utils.DownloadError:

        return jsonify({
            "success": False,
            "error":
                "Unable to access this Instagram media. Make sure the post is public and the URL is correct."
        }), 404

    except Exception as error:

        print(
            "PaceFetch error:",
            repr(error)
        )

        return jsonify({
            "success": False,
            "error":
                "PaceFetch could not process this Instagram URL."
        }), 500


@app.route("/", methods=["GET"])
def health():

    return jsonify({
        "service": "PaceFetch",
        "status": "online",
        "message":
            "PaceFetch Instagram downloader API is running."
    })


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        )
      )
