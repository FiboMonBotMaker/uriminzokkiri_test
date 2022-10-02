from datetime import time
from math import ceil
from discord.ext import commands, tasks
from discord.ui import View, button, Button, Modal, InputText, Select
from discord import Option, OptionChoice, Embed, Color, SlashCommandGroup, Interaction, ApplicationContext, Permissions, FFmpegPCMAudio, PCMVolumeTransformer, SelectOption
from lib import uriminzokkiri as uz
import asyncio
import aiohttp
import aiofiles
from typing import List


class QuickPushQuiz(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.update.start()

    async def update_music_overviews(self):
        print("update")
        self.music_overviews = await uz.search(skey="", lang="kor")
        self.amo_of_songs = len(self.music_overviews)
        self.num_of_pages = ceil(self.amo_of_songs/25)
        print(f"musics{self.amo_of_songs} pages{self.num_of_pages}")

        # 北の国の音楽を検索します
    music_command = SlashCommandGroup(
        name="k_music",
        description="北の音楽を聴くためのBOT"
    )

    setup_command = SlashCommandGroup(
        name="setup",
        description="スタティックな位置に配置するためのあれ",
        default_permissions=Permissions(administrator=True)
    )

    @setup_command.command(name="channel", description="呼び出したチャンネルに再生ボタンを固定します")
    async def channel(self, ctx: ApplicationContext):
        await ctx.response.send_message(content="Set up channel", ephemeral=True)
        embed = Embed(
            title=f"Pages 1/{self.num_of_pages}", color=Color.brand_red())
        for i in range(0, 25 if self.num_of_pages > 25 else len(self.num_of_pages)):
            m = self.music_overviews[i]
            embed.add_field(name=m.title, value=f"NO:{m.no}\n{m.sub_title}")
        await ctx.channel.send(embed=embed, view=BaseView(music_overviews=self.music_overviews))
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

        word: str = word
        musiclist = await uz.search(skey=word, lang=lang)
        result = "\n".join([f"{v.no}: {v.title}" for v in musiclist])
        if len(result) == 0:
            await ctx.response(content=f"**{word}**が含まれる曲は見つかりませんでした。")
            return

        await ctx.interaction.response.send_message(content="player set", view=BaseView(music_overviews=musiclist))

    @tasks.loop(time=[time(hour=h) for h in range(24)])
    async def update(self):
        await self.update_music_overviews()

    @update.before_loop
    async def update_init(self):
        print("start")
        await self.update_music_overviews()

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
        self.amo_of_songs = len(self.music_overviews)
        self.num_of_pages = ceil(self.amo_of_songs/25)
        self.index = 0

        self.add_item(
            MusicSelecter(
                [
                    SelectOption(label=v.title, value=str(i+(25*self.index)))
                    for i, v in enumerate(
                        self.music_overviews[
                            self.index*25:
                                ((self.index+1)*25)
                                if len(self.music_overviews) >= (self.index+1)*25
                                else len(self.music_overviews)
                        ]
                    )
                ]
            )
        )
        self.now_select = self.children[-1]

    @button(label="検索", row=2)
    async def re_search(self, _: Button, interaction: Interaction):
        await interaction.response.send_modal(modal=ReSearchModal())

    @button(label="PREV", row=3)
    async def prev(self, button: Button, interaction: Interaction):
        self.index -= 1
        music = [v for v in self.music_overviews]
        embed = Embed(title="music list", color=Color.brand_red())
        for v in music:
            embed.add_field(name=v.title, value=f"NO:{v.no}\n{v.sub_title}")
        self.remove_item(MusicSelecter)
        self.add_item(
            MusicSelecter(
                [
                    SelectOption(label=v.title, value=str(i+(25*self.index)))
                    for i, v in enumerate(music)
                ]
            )
        )

        await interaction.response.edit_message(embed=embed, view=self)

    @button(label="NEXT", row=3)
    async def next(self, button: Button, interaction: Interaction):
        self.index += 1
        music = [v for v in self.music_overviews[self.index*25:((self.index+1)*25)
                                                 if len(self.music_overviews) >= (self.index+1)*25
                                                 else len(self.music_overviews)]]
        embed = Embed(
            title=f"Pages {self.index+1}/{self.num_of_pages}", color=Color.brand_red())
        for v in music:
            embed.add_field(name=v.title, value=f"NO:{v.no}\n{v.sub_title}")
        self.remove_item(self.now_select)
        self.add_item(
            MusicSelecter(
                [
                    SelectOption(label=v.title[0:100 if len(v.title) > 100 else len(
                        v.title)], value=str(i+(25*self.index)))
                    for i, v in enumerate(music)
                ]
            )
        )
        self.now_select = self.children[-1]

        await interaction.response.edit_message(embed=embed, view=self)

    @button(label="EXIT", row=4)
    async def exit(self, button: Button, interaction: Interaction):
        self.index += 1
        await interaction.response.edit_message(content="STOP MUSIC", view=self)
        vc = interaction.guild.voice_client
        if vc:
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
        for f in asyncio.as_completed([v.get_music() for v in music_overviews]):
            await f
        await interaction.response.send_message(view=BaseView(music_overviews=music_overviews))


class MusicSelecter(Select["BaseView"]):
    def __init__(self, options: List[SelectOption] = ...) -> None:
        super().__init__(placeholder="再生する音楽を選択してください", options=options,)

    async def callback(self, interaction: Interaction):
        vc = interaction.guild.voice_client
        if not vc:
            vc = await interaction.user.voice.channel.connect(timeout=10)

        view: BaseView = self.view
        music = view.music_overviews[int(self.values[0])]
        await interaction.response.edit_message(content=f"Play -> **{music.title}**")
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
