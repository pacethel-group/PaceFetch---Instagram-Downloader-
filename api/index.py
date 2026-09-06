import re
from urllib.parse import urlparse

import instaloader
from flask import Flask, jsonify, request


app = Flask(__name__)


# --------------------------------------------------
# INSTALOADER
# --------------------------------------------------

L = instaloader.Instaloader(
    download_pictures=False,
    download_videos=False,
    download_video_thumbnails=False,
    save_metadata=False,
    compress_json=False,
    quiet=True
)


# --------------------------------------------------
# INSTAGRAM URL VALIDATION
# --------------------------------------------------

def is_instagram_url(url):
    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        hostname = (
            parsed.hostname or ""
        ).lower()

        hostname = re.sub(
            r"^www\.",
            "",
            hostname
        )

        return (
            hostname == "instagram.com"
            or hostname.endswith(".instagram.com")
        )

    except Exception:
        return False


# --------------------------------------------------
# EXTRACT INSTAGRAM SHORTCODE
# --------------------------------------------------

def extract_shortcode(url):

    parsed = urlparse(url)

    path = parsed.path.strip("/")

    parts = [
        part
        for part in path.split("/")
        if part
    ]

    if not parts:
        return None

    supported_types = {
        "p",
        "reel",
        "reels",
        "tv"
    }

    if len(parts) >= 2:

        content_type = parts[0]
        shortcode = parts[1]

        if content_type in supported_types:
            return shortcode

    return None


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.route("/api", methods=["GET"])
@app.route("/api/", methods=["GET"])
def api_health():

    return jsonify({
        "success": True,
        "service": "PaceFetch",
        "status": "online",
        "message": "PaceFetch Instagram API is running."
    })


# --------------------------------------------------
# DOWNLOAD INFORMATION
# --------------------------------------------------

@app.route("/api/download", methods=["GET"])
def download():

    instagram_url = request.args.get(
        "url",
        ""
    ).strip()


    if not instagram_url:

        return jsonify({
            "success": False,
            "error":
                "Instagram URL is required."
        }), 400


    if not is_instagram_url(
        instagram_url
    ):

        return jsonify({
            "success": False,
            "error":
                "Only Instagram URLs are supported."
        }), 400


    shortcode = extract_shortcode(
        instagram_url
    )


    if not shortcode:

        return jsonify({
            "success": False,
            "error":
                "Could not identify the Instagram post or Reel."
        }), 400


    try:

        post = instaloader.Post.from_shortcode(
            L.context,
            shortcode
        )


        # --------------------------------------------------
        # BASIC INFORMATION
        # --------------------------------------------------

        title = (
            post.caption
            or "Instagram media"
        )

        title = title.strip()

        if len(title) > 180:
            title = title[:180] + "..."


        thumbnail = (
            post.url
            or ""
        )


        # --------------------------------------------------
        # VIDEO
        # --------------------------------------------------

        if post.is_video:

            media_url = (
                post.video_url
                or ""
            )

            return jsonify({

                "success": True,

                "type": "video",

                "title": title,

                "thumbnail":
                    thumbnail,

                "media_url":
                    media_url,

                "filename":
                    f"PaceFetch-{shortcode}.mp4",

                "shortcode":
                    shortcode

            })


        # --------------------------------------------------
        # PHOTO
        # --------------------------------------------------

        media_url = (
            post.url
            or ""
        )


        return jsonify({

            "success": True,

            "type": "image",

            "title": title,

            "thumbnail":
                media_url,

            "media_url":
                media_url,

            "filename":
                f"PaceFetch-{shortcode}.jpg",

            "shortcode":
                shortcode

        })


    except instaloader.exceptions.InstaloaderException as error:

        print(
            "Instaloader error:",
            repr(error)
        )

        return jsonify({

            "success": False,

            "error":
                "Instagram could not provide this public media. Check that the post is public and the URL is correct."

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


# --------------------------------------------------
# ROOT
# --------------------------------------------------

@app.route("/", methods=["GET"])
def home():

    return jsonify({

        "service":
            "PaceFetch",

        "status":
            "online",

        "message":
            "PaceFetch Instagram downloader backend."

    })
