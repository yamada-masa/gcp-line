# GCP設定
PROJECT = ""
ZONE = ""
INSTANCE_NAME = ""

MACHINE_TYPE_SUFFIX = f"zones/{ZONE}/machineTypes/"
MACHINE_TYPE_DICT = {"default": "e2-highcpu-2", "high": "e2-highcpu-4"}

# LINE設定
USER_IDS = ["", ""]

CHANNEL_SECRET = ""
CHANNEL_ACCESS_TOKEN = ""

DICTIONARY: dict = {
    "started": "起動しました",
    "stopped": "停止しました",
    "changed": "変更しました",
    "alreadyStarted": "すでに起動しています",
    "alreadyStopped": "すでに停止しています",
    "notSupportedFunction": "その操作はサポートしていません",
    "notAuthorized": "権限がありません",
    "start": "起動",
    "stop": "停止",
    "scaleUp": "スペックアップ",
    "scaleDown": "スペックダウン",
    "machineType": "現在のマシンタイプ{}",
}
