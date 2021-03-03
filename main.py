import base64
import hashlib
import hmac

import googleapiclient.discovery
from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
from linebot.models import TextSendMessage
from oauth2client.client import GoogleCredentials

from config import (
    CHANNEL_ACCESS_TOKEN,
    CHANNEL_SECRET,
    DICTIONARY,
    INSTANCE_NAME,
    MACHINE_TYPE_DICT,
    MACHINE_TYPE_SUFFIX,
    PROJECT,
    USER_IDS,
    ZONE,
)


class MineCraftServer:
    def __init__(self, project: str, zone: str, instance_name: str):
        credentials = GoogleCredentials.get_application_default()
        self.service = googleapiclient.discovery.build(
            "compute", "v1", credentials=credentials, cache_discovery=False
        )
        self.project = project
        self.zone = zone
        self.instance_name = instance_name
        self.instance = (
            self.service.instances()
            .get(project=project, zone=zone, instance=instance_name)
            .execute()
        )

    def start(self) -> bool:
        if self.instance["status"] == "TERMINATED":
            self.service.instances().start(
                project=self.project, zone=self.zone, instance=self.instance_name
            ).execute()
            return True
        return False

    def stop(self) -> bool:
        if self.instance["status"] == "RUNNING":
            self.service.instances().stop(
                project=self.project, zone=self.zone, instance=self.instance_name
            ).execute()
            return True
        return False

    def scale(self, up: bool) -> bool:
        if self.instance["status"] == "TERMINATED":
            after_type = (
                MACHINE_TYPE_DICT["high"] if up else MACHINE_TYPE_DICT["default"]
            )
            if not self.instance["machineType"].endswith(after_type):
                self.instance["machineType"] = MACHINE_TYPE_SUFFIX + after_type
                self.service.instances().update(
                    project=self.project,
                    zone=self.zone,
                    instance=self.instance_name,
                    body=self.instance,
                ).execute()
            return True
        return False

    def get_machine_type_str(self) -> str:
        machine_type = self.instance["machineType"]
        return machine_type[machine_type.rfind("/") + 1 :]

    def is_machine_type_default(self) -> bool:
        machine_type = self.instance["machineType"]
        return (
            machine_type[machine_type.rfind("/") + 1 :] == MACHINE_TYPE_DICT["default"]
        )


class LineMineCraft:
    def __init__(self, request, server: MineCraftServer):
        payload = request.get_json(silent=True)
        self.body = request.get_data()
        self.user_id = payload["events"][0]["source"]["userId"]
        self.reply_token = payload["events"][0]["replyToken"]
        self.type = payload["events"][0]["type"]
        self.text = payload["events"][0]["message"]["text"]
        self.signature = request.headers.get("x-line-signature")
        self.mine_craft_server = server

    def auth(self) -> bool:
        body_hash = hmac.new(
            CHANNEL_SECRET.encode("utf-8"), self.body, hashlib.sha256
        ).digest()
        signature = base64.b64encode(body_hash)

        if signature.decode("utf-8") != self.signature:
            print(f"invalid signature: {signature} header: {self.signature}")
            self.response(DICTIONARY["NotAuthorized"])
            return False

        if self.user_id not in USER_IDS:
            print(self.user_id)
            return False

        return True

    def response(self, message: str) -> None:
        line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

        try:
            line_bot_api.reply_message(self.reply_token, TextSendMessage(text=message))
        except LineBotApiError as e:
            print(e)

    def start(self) -> bool:
        ret = self.mine_craft_server.start()
        if ret:
            self.response(
                DICTIONARY["started"]
                + DICTIONARY["machineType"].format(
                    self.mine_craft_server.get_machine_type_str()
                )
            )
        else:
            self.response(DICTIONARY["alreadyStarted"])
        return ret

    def stop(self) -> bool:
        ret = self.mine_craft_server.stop()
        if ret:
            self.response(DICTIONARY["stopped"])
            if not self.mine_craft_server.is_machine_type_default():
                self.scale(False)
        else:
            self.response(DICTIONARY["alreadyStopped!"])
        return ret

    def scale(self, up: bool) -> bool:
        ret = self.mine_craft_server.scale(up)
        if ret:
            self.response(DICTIONARY["changed"])
        else:
            self.response(DICTIONARY["alreadyStarted!"])
        return ret


def line(request):
    line_minecraft = LineMineCraft(
        request, MineCraftServer(PROJECT, ZONE, INSTANCE_NAME)
    )
    if not line_minecraft.auth():
        return

    if line_minecraft.type == "message":
        if line_minecraft.text == DICTIONARY["start"]:
            line_minecraft.start()
        elif line_minecraft.text == DICTIONARY["stop"]:
            line_minecraft.stop()
        elif line_minecraft.text == DICTIONARY["scaleUp"]:
            line_minecraft.scale(True)
        elif line_minecraft.text == DICTIONARY["scaleDown"]:
            line_minecraft.scale(False)
        else:
            line_minecraft.response(DICTIONARY["notSupportedFunction"])
