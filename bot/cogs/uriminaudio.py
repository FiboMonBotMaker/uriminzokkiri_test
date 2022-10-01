from discord.ext import commands
from discord.ui import View, button, Button
from discord import Option, OptionChoice, SlashCommandGroup, Interaction, ApplicationContext, Permissions, FFmpegPCMAudio, PCMVolumeTransformer, SelectOption
from lib import uriminzokkiri as uz
import asyncio
import aiohttp
import aiofiles
from typing import List
from discord import Interaction, ButtonStyle, Embed, Color, SelectOption, Interaction, FFmpegPCMAudio, PCMVolumeTransformer
from discord.ui import Button, View, button, Select
from discord.ui import View, button, Button, Modal, InputText
import aiohttp


class QuickPushQuiz(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    # 北の国の音楽を検索します
    music_command = SlashCommandGroup(
        name="k_music",
        description="北の音楽を聴くためのBOT"
    )

    # playlist_command = music_command.subcommands(
    #     name="playlist",
    #     description="プレイリストを作ったりなんだり"

    # )

    @music_command.command(name="search", description="ワード検索")
    async def search(
            self,
            ctx: ApplicationContext,
            word: Option(str, description="いろんな言語で検索できます"),
            lang: Option(
                str,
                default="kor",
                choices=[
                    OptionChoice(name="朝鮮語", value="kor"),
                    OptionChoice(name="日本語", value="jpn"),
                    OptionChoice(name="英語", value="eng"),
                    OptionChoice(name="ロシア語", value="rus"),
                    OptionChoice(name="中国語", value="chn"),
                ],
            )
    ):
        global vc
        vc = ctx.voice_client
        if not vc:
            vc = await ctx.author.voice.channel.connect()

        word: str = word
        musiclist = await uz.search(skey=word, lang=lang)
        result = "\n".join([f"{v.no}: {v.title}" for v in musiclist])
        if len(result) == 0:
            await ctx.response(content=f"**{word}**が含まれる曲は見つかりませんでした。")
            return

        await ctx.interaction.response.send_message(content="player set", view=BaseView(music_overviews=musiclist))

    # @playlist_command.command(name="add", description="プレイリストに音楽を追加します")
    # async def search(
    #     self,
    #     ctx: ApplicationContext,
    #     no: Option(int, description="いろんな言語で検索できます"),
    # ):


class BaseView(View):
    def __init__(self, music_overviews: List[uz.MusicOverview]):
        super().__init__(timeout=None)
        self.music_overviews = music_overviews
        self.index = 0

        self.add_item(
            MusicSelecter(
                [
                    SelectOption(label=v.title, value=str(i+(25*self.index)))
                    for i, v in enumerate(
                        self.music_overviews[
                            self.index*25:
                                ((self.index+1)*25)-1
                                if len(self.music_overviews) >= (self.index+1)*25
                                else len(self.music_overviews)-1
                        ]
                    )
                ]
            )
        )

    @button(label="検索", row=4)
    async def re_search(self, _: Button, interaction: Interaction):
        await interaction.response.send_modal(modal=ReSearchModal())

    @button(label="とじる", row=4)
    async def hoge(self, button: Button, interaction: Interaction):
        button.disabled = True
        await interaction.response.edit_message(content="Bye", view=self)
        await interaction.delete_original_message(delay=5)
        await vc.disconnect()


class ReSearchModal(Modal):
    def __init__(self) -> None:
        super().__init__(title="サーチするよ")
        self.add_item(InputText(
            label="検索わーど",
            placeholder="공격전이다",
            required=True
        ))

    async def callback(self, interaction: Interaction):
        word = self.children[0].value
        music_overviews = await uz.search(skey=word)

        if len(music_overviews) == 0:
            await interaction.response.send_message(content=f"{word}はみつかんないでした")
            return
        await interaction.response.send_message(view=BaseView(music_overviews=music_overviews))


class MusicSelecter(Select["BaseView"]):
    def __init__(self, options: List[SelectOption] = ...) -> None:
        super().__init__(placeholder="再生する音楽を選択してください", options=options,)

    async def callback(self, interaction: Interaction):
        view: BaseView = self.view
        music = view.music_overviews[int(self.values[0])]
        await interaction.response.send_message(content=f"Play -> **{music.title}**")
        m = await music.get_music()
        vc.stop()
        async with aiohttp.ClientSession() as session:
            async with session.get(m.src) as resp:
                if resp.status == 200:
                    f = await aiofiles.open("test.mp3", mode="wb")
                    await f.write(await resp.read())
                    await f.close()

        vc.play(PCMVolumeTransformer(FFmpegPCMAudio("test.mp3"), 0.5))


def setup(bot: commands.Bot):
    bot.add_cog(QuickPushQuiz(bot))
