import aiohttp
import json
import re
from unicodedata import normalize


url = "http://uriminzokkiri.com/index.php?ptype=cmusic"

endpoint = "http://uriminzokkiri.com/"

langs = [
    "kor",  # 조선어 (Korean)
    "eng",  # English
    "rus",  # Русский (Russian)
    "chn",  # 中国语 (Chinese)
    "jpn",  # 日本語 (Japanese) (there are no music in japanese page)
]


def _bool(YN):
    if YN == "Y":
        return True
    elif YN == "N":
        return False
    else:
        return None


class Music:  # Music class from music number
    def __init__(self, music: dict):
        self.title: str = re.sub(r"(<([^>]+)>)", "", music[0]["title"])
        self.no: int = int(music[0]["no"])
        self.url: str = endpoint + \
            "index.php?ptype=cmusic&mtype=view&no=" + str(self.no)
        self.src: str = endpoint + music[0]["src"].strip("./")
        self.imgsrc: str = endpoint + music[0]["imgsrc"].strip("./")
        self.feels = [
            self.Feel(feel) for feel in music[0]["feels"]
        ] if "feels" in music[0] else []

    def __str__(self):
        return self.title

    class Feel:
        def __init__(self, feel):
            self.address: str = feel["address"]
            self.bon_send: str = _bool(feel["bon_send"])
            self.categ1: int = int(feel["categ1"])
            self.categ2: int = int(feel["categ2"])
            self.categ3: int = int(feel["categ3"])
            self.contents_html: str = feel["contents"]
            self.contents: str = normalize(
                "NFKD",
                re.sub(r"(<([^>]+)>)", "", feel["contents"])
            )
            self.email: str = feel["email"]
            self.email_isview: bool = _bool(feel["email_isview"])
            self.emoticon: int = int(feel["emoticon"])
            self.file_name: str = feel["file_name"]
            self.firstpage_isview: bool = _bool(feel["firstpage_isview"])
            self.hit: int = int(feel["hit"])
            self.ip: str = feel["ip"]
            self.is_view: bool = _bool(feel["is_view"])
            self.job: str = feel["job"]
            self.listpage_isview: bool = _bool(feel["listpage_isview"])
            self.main_flag: int = int(feel["main_flag"])
            self.name: str = feel["name"]
            self.new_file_name: str = feel["new_file_name"]
            self.new_no: int = int(feel["new_no"])
            self.no: int = int(feel["no"])
            self.reg_date: str = feel["reg_date"]
            self.reg_time: str = feel["reg_time"]
            self.title: str = re.sub(r"(<([^>]+)>)", "", feel["title"])
            self.view_flag: bool = _bool(feel["view_flag"])

        def __str__(self):
            return self.name


class MusicOverview:
    def __init__(self, music: dict):
        self.no: int = int(music["no"])
        self.title: str = re.sub(r"(<([^>]+)>)", "", music["title"])
        self.sub_title: str = music["sub_title"]
        self.reg_date: str = music["reg_date"]
        self.categ1: int = int(music["categ1"])
        self.categ2: int = int(music["categ2"])
        self.categ3: int = int(music["categ3"])
        self.categ3_name: str = music["categ3_name"]
        self.file_name: str = music["file_name"]
        self.firstpage_isview: bool = _bool(music["firstpage_isview"])
        self.hit: int = int(music["hit"])
        self.is_new: bool = _bool(music["is_new"])
        self.is_view: bool = _bool(music["is_view"])
        self.key_word: str = music["key_word"]
        self.lang_kind: str = music["lang_kind"]
        self.listpage_isview: bool = _bool(music["listpage_isview"])
        self.old_filename: str = music["old_filename"]
        self.special_no: int = int(music["special_no"])
        self.summary: str = music["summary"]
        self.view_order: int = int(music["view_order"])

    def __str__(self):
        return self.title

    async def get_music(self):
        return await get_music(self.no)


async def get_music(no: int):
    async with aiohttp.ClientSession() as session:
        async with session.post(url=endpoint+"index.php?ptype=cmusic&mtype=play", data={"no": str(no)+"pl"}) as resp:
            data = await resp.read()
            j = json.loads(data)
            return Music(j)


async def search(skey: str = "", lang: str = "kor") -> list[MusicOverview]:
    data = {
        "no_pagination": str(1),
        "num_per_page": str(10000),
        "skey": skey,
        "orderby": "reg_date desc",
    }

    async def __search(url: str, data: dict[str, str]) -> list[MusicOverview]:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, data=data) as resp:
                data = await resp.read()
                j = json.loads(data)
                return [MusicOverview(m) for m in j["lists"]]

    if lang == "kor":
        return await __search(endpoint+"index.php?ptype=cmusic&mtype=writeList", data)
    elif lang in langs:
        data["lang"] = lang
        return await __search(endpoint+"index.php?ptype=cfomus&mtype=writeList", data)
    else:
        raise AttributeError(
            f"Any of the attributes that can be specified in lang -> {langs}")
