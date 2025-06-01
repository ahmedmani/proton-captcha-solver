from mitmproxy import http
import json

class CaptchaReplacer:
    def response(self, flow: http.HTTPFlow) -> None:
        if "verify-api.proton.me/core/v4/captcha" in flow.request.pretty_url:
            resp_path = "\\".join(__file__.split("\\")[:-1]) + "\\captcha_response.html"

            with open(resp_path, "r") as f:
                body = f.read()

            flow.response = http.Response.make(
                200,
                body,
                {"Content-Type": "text/html; charset=UTF-8"}
            )

addons = [CaptchaReplacer()]
